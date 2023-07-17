#include <picojson.h>

#include <algorithm>
#include <highfive/H5Easy.hpp>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

#include "osm_filter.hpp"
#include "polygonize.hpp"
#include "triangulation.hpp"

#ifdef HAVE_JQ
#include <jqrunner.hpp>
#endif

// todo: replace with boost geometry
using Point = std::vector<double>;
using Linestring = std::vector<Point>;
using Polygon = std::vector<Linestring>;

// struct IndirectionAppender(std::string data_name, std::string index_name,
// std::vector<double> row)

template <typename dtype, int DIM, int CACHE_SIZE = 1024 * 1024 * 1024>
class IndirectionAppender {
private:
  HighFive::DataSet &data, &index;

public:
  IndirectionAppender(HighFive::DataSet &data, HighFive::DataSet &index)
      : data(data), index(index) {}
  ~IndirectionAppender() { flush(); };

  std::vector<std::vector<dtype>> ccache;
  std::vector<std::vector<uint32_t>> icache;

  void flush() {
    // Flush data
    if (ccache.size() != 0) {
      auto size = data.getDimensions();
      auto start = size[0];
      size[0] += ccache.size();
      data.resize(size);
      data.select({start, 0}, {ccache.size(), DIM}).write(ccache);
      ccache.clear();
    }
    if (icache.size() != 0) {
      auto size = index.getDimensions();
      auto start = size[0];
      size[0] += icache.size();
      index.resize(size);
      index.select({start, 0}, {icache.size(), DIM}).write(icache);
      icache.clear();
    }
  }

  void operator()(const std::vector<std::vector<dtype>> &row) {
    // Warning: row must be contiguous and strictly DIM
    auto start = data.getDimensions()[0] + ccache.size();
    auto end = start + row.size();
    ccache.insert(ccache.end(), row.cbegin(), row.cend());
    icache.push_back(
        {static_cast<uint32_t>(start), static_cast<uint32_t>(end)});
    if (ccache.size() > CACHE_SIZE)
      flush();
  }
};

void _resolve_osm_ways(std::string inputfile, std::string method,
                       std::string query = ".") {
  std::cout << "Resolving ways..." << std::endl;
  H5Easy::File file(inputfile, H5Easy::File::ReadWrite);

#ifdef HAVE_JQ
  std::cout << "Activating a JQrunner for ways triangulation with " << query
            << std::endl;
  JQRunner jq(query);
#endif

  // load node indices
  auto nodes = H5Easy::load<std::vector<uint64_t>>(file, "/osm/nodes");
  std::cout << "Node count: " << nodes.size() << std::endl;

  std::map<uint64_t, uint64_t> osm2row;
  for (size_t i = 0; i < nodes.size(); i++)
    osm2row[nodes[i]] = i;
  nodes.clear();

  // create datasets
  if (!file.getGroup("osm").exist("linestrings")) {
    HighFive::DataSpace ds =
        HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED, 2});
    HighFive::DataSetCreateProps props;
    props.add(HighFive::Chunking(std::vector<hsize_t>{1024 * 1024, 2}));
    props.add(HighFive::Deflate(9));

    file.getGroup("osm").createDataSet("linestrings", ds,
                                       HighFive::AtomicType<double>(), props);
    file.getGroup("osm").createDataSet("linestrings_idx", ds,
                                       HighFive::AtomicType<uint32_t>(), props);
    file.getGroup("osm").createDataSet("ways_triangles", ds,
                                       HighFive::AtomicType<double>(), props);
    file.getGroup("osm").createDataSet("ways_triangles_idx", ds,
                                       HighFive::AtomicType<uint32_t>(), props);
  }

  // open created datasets
  HighFive::DataSet linestrings_ds = file.getDataSet("/osm/linestrings");
  HighFive::DataSet linestrings_idx = file.getDataSet("/osm/linestrings_idx");
  HighFive::DataSet triangles_ds = file.getDataSet("/osm/ways_triangles");
  HighFive::DataSet triangles_idx = file.getDataSet("/osm/ways_triangles_idx");

  IndirectionAppender<double, 2> emit_linestring(linestrings_ds,
                                                 linestrings_idx);
  IndirectionAppender<double, 2> emit_triangles(triangles_ds, triangles_idx);

  // process ways
  size_t n_ways = H5Easy::getSize(file, "/osm/ways");
  std::cout << "Way count: " << n_ways << std::endl;

  HighFive::DataSet ways_refs = file.getDataSet("/osm/ways_refs");
  HighFive::DataSet ways_attr = file.getDataSet("/osm/ways_attr");

  HighFive::DataSetAccessProps aprops;
  aprops.add(HighFive::Caching(512, 64 * 1024 * 1024, 0.5));
  HighFive::DataSet nodes_coords = file.getDataSet("/osm/nodes_coords", aprops);
  // H5Pset_chunk_cache( pid, 100, 10000, 0.5)

  for (size_t i = 0; i < n_ways; i++) {
    // fetch refs
    std::vector<std::string> result;
    ways_refs.select({i, 0}, {1, 1}).read(result);
    std::stringstream ss(result[0]);
    std::string item;
    std::vector<uint64_t> elems;
    while (std::getline(ss, item, ',')) {
      elems.push_back(std::stoull(item));
    }

    // check the linestring is closed (not, for example, a river)
    // if (elems.front() != elems.back()) {
    //   continue;  // this is not a closed ring, hence, never an area
    // }

    // assemble coordinates
    Linestring linestring;
    for (const auto &e : elems) {
      auto row = osm2row[e];
      Point pointdata;
      nodes_coords.select({row, 0}, {1, 2}).read(pointdata);
      linestring.push_back({pointdata[0], pointdata[1]});
    }

    // fetch way tags
    std::vector<std::string> attr;
    ways_attr.select({i, 0}, {1, 1}).read(attr);
    // MARK: Here we could filter withcontinue?
    // #ifdef HAVE_JQ
    //     if (jq(attr[0]) == "") {
    //       continue;
    //     }
    // #endif

    // deserialize tags
    picojson::value v;
    std::string err = picojson::parse(v, attr[0]);
    if (!err.empty()) {
      std::cerr << err << std::endl;
    }

    // assemble triangles as a contiguous set of coordinates (linestring)
    std::vector<Point> triangles;
// this is an incompatible choice as filtering tags can destroy these
// assumptions for the future, I aim for having selection of triangulation done
// in python based on a JQ query and not here. Hence, a hack that brings this
// behavior to python, but keeps your idea for atlashdf binary for the moment
#ifdef HAVE_JQ
    // std::cout << "JQ: " << jq(attr[0]) << std::endl;
    if (osm::matches(v, osm::AREA_KEYS, osm::AREA_TAGS, osm::AREA_TAGS_NOT) &&
        attr[0] != "" && jq(attr[0]) != "")
#else
    if (osm::matches(v, osm::AREA_KEYS, osm::AREA_TAGS, osm::AREA_TAGS_NOT))
#endif
    {
      // triangulate
      if (method == "earcut") {
        triangles = triangulation::earcut({linestring});
      } else if (method == "boost") {
        triangles = triangulation::boost({linestring});
      }
    }
    // load triangles
    emit_triangles(triangles);

    // load linestrings
    emit_linestring(linestring);

#ifdef DEBUG_TRUNCATE
    // Debug Truncate will run this operation, but only to 1% of the input
    if ((double)i / (double)n_ways > 0.01)
      break;
#endif
#ifdef SHOW_PROGRESS
    if (i % 100 == 0)
      std::cout << "Progress: " << (double)i / (double)n_ways << "\r";
    std::cout.flush();
#endif
  }
}

void _resolve_osm_relations(std::string inputfile, std::string method,
                            std::string query = ".") {
  std::cout << "Resolving relations..." << std::endl;
  H5Easy::File file(inputfile, H5Easy::File::ReadWrite);

#ifdef HAVE_JQ
  std::cout << "Activating a JQrunner for relations triangulation with "
            << query << std::endl;
  JQRunner jq(query);
#endif

  // load linestring indices
  auto ways = H5Easy::load<std::vector<uint64_t>>(file, "/osm/ways");
  std::cout << "Way count: " << ways.size() << std::endl;

  std::map<uint64_t, uint64_t> osm2row;
  for (size_t i = 0; i < ways.size(); i++)
    osm2row[ways[i]] = i;
  ways.clear();

  // create datasets
  if (!file.getGroup("osm").exist("relations_triangles")) {
    HighFive::DataSpace ds =
        HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED, 2});
    HighFive::DataSetCreateProps props;
    props.add(HighFive::Chunking(std::vector<hsize_t>{1024 * 1024, 2}));
    props.add(HighFive::Deflate(9));

    file.getGroup("osm").createDataSet("relations_triangles", ds,
                                       HighFive::AtomicType<double>(), props);
    file.getGroup("osm").createDataSet("relations_triangles_idx", ds,
                                       HighFive::AtomicType<uint32_t>(), props);
  }

  // open triangle dataset
  HighFive::DataSet triangles_ds = file.getDataSet("/osm/relations_triangles");
  HighFive::DataSet triangles_idx =
      file.getDataSet("/osm/relations_triangles_idx");

  // create indirection appender for triangles
  IndirectionAppender<double, 2> emit_triangles(triangles_ds, triangles_idx);

  // process relations
  size_t n_relations = H5Easy::getSize(file, "/osm/relations");
  std::cout << "Relation count: " << n_relations << std::endl;

  HighFive::DataSet relations_refs = file.getDataSet("/osm/relations_refs");
  HighFive::DataSet relations_attr = file.getDataSet("/osm/relations_attr");

  HighFive::DataSetAccessProps aprops;
  aprops.add(HighFive::Caching(512, 64 * 1024 * 1024, 0.5));
  HighFive::DataSet linestrings = file.getDataSet("/osm/linestrings", aprops);
  HighFive::DataSet linestrings_idx =
      file.getDataSet("/osm/linestrings_idx", aprops);

  for (size_t i = 0; i < n_relations; i++) {
    // fetch relation tags
    std::vector<std::string> attr;
    relations_attr.select({i, 0}, {1, 1}).read(attr);

#ifdef HAVE_JQ
    if (attr[0] == "" || jq(attr[0]) == "") {
      emit_triangles({});
      continue;
    }
#else
    // deserialize tags
    picojson::value tags;
    auto tags_err = picojson::parse(tags, attr[0]);
    if (!tags_err.empty())
      std::cerr << tags_err << std::endl;

    // process only type=multipolygon
    if (!tags.contains("type") || tags.get("type").to_str() != "multipolygon") {
      emit_triangles({});
      continue;
    }
#endif

    // fetch refs (members)
    std::vector<std::string> refs;
    relations_refs.select({i, 0}, {1, 1}).read(refs);

    picojson::value members;
    auto members_err = picojson::parse(members, refs[0]);
    if (!members_err.empty())
      std::cerr << members_err << std::endl;

    // fetch linestrings
    std::vector<linestring> outers;
    std::vector<linestring> inners;

    for (const auto &m : members.get<picojson::array>()) {
      // only process well formed members
      auto role = m.get("role").get<std::string>();
      if (!(role == "outer" || role == "inner"))
        continue;

      // read linestring
      Linestring linestringdata;
      std::vector<uint32_t> idx;
      auto row = osm2row[(size_t)m.get("member_id").get<double>()];
      linestrings_idx.select({row, 0}, {1, 2}).read(idx);
      linestrings.select({idx[0], 0}, {idx[1] - idx[0], 2})
          .read(linestringdata);

      if (role == "outer") {
        outers.push_back(linestringdata);
      } else if (role == "inner") {
        inners.push_back(linestringdata);
      }
    }

    // assemble linestrings (polygonize)
    std::vector<Polygon> mp = polygonize(outers, inners);

    // triangulate
    std::vector<Point> triangles;
    for (const auto &p : mp) {
      if (method == "earcut") {
        for (const auto &t : triangulation::earcut(p))
          triangles.push_back(t);

      } else if (method == "boost") {
        for (const auto &t : triangulation::boost(p))
          triangles.push_back(t);
      }
    }

    // load triangles
    emit_triangles(triangles);

#ifdef DEBUG_TRUNCATE
    // Debug Tuncate will run this operation, but only to 1% of the input
    if ((double)i / (double)n_ways > 0.01)
      break;
#endif
#ifdef SHOW_PROGRESS
    if (i % 100 == 0)
      std::cout << "Progress: " << (double)i / (double)n_relations << "\r";
    std::cout.flush();
#endif
  }
}

bool resolve_osm_geometry(std::string inputfile, std::string output,
                          std::string method, std::string nodes_query,
                          std::string ways_query, std::string relations_query) {
  std::cout << "Resolving geometries using " << method << std::endl;
  _resolve_osm_ways(inputfile, method, ways_query);
  _resolve_osm_relations(inputfile, method, relations_query);
  return true;
}
