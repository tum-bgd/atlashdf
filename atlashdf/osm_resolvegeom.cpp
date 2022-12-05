#include <algorithm>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

#include <highfive/H5Easy.hpp>
#include <picojson.h>

#include "traingulation.hpp"

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
    {
      auto size = data.getDimensions();
      auto start = size[0];
      size[0] += ccache.size();
      data.resize(size);
      data.select({start, 0}, {ccache.size(), DIM}).write(ccache);
      ccache.clear();
    }
    {
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

const std::vector<std::string> AREA_KEYS = {
    "building", "landuse",  "amenity", "shop",        "building:part",
    "boundary", "historic", "place",   "area:highway"};

const std::map<std::string, std::vector<std::string>> AREA_TAGS = {
    {"area", {"yes"}},
    {"waterway", {"riverbank"}},
    {"highway", {"rest_area", "services", "platform"}},
    {"railway", {"platform"}},
    {"natural",
     {"water",     "wood",      "scrub",    "wetland", "grassland", "heath",
      "rock",      "bare_rock", "sand",     "beach",   "scree",     "bay",
      "glacier",   "shingle",   "fell",     "reef",    "stone",     "mud",
      "landslide", "sinkhole",  "crevasse", "desert"}},
    {"aeroway", {"aerodrome"}}};

const std::map<std::string, std::vector<std::string>> AREA_TAGS_NOT = {
    {"leisure", {"picnic_table", "slipway", "firepit"}}};

void _resolve_osm_ways(std::string inputfile) {
  std::cout << "Resolving ways..." << std::endl;
  H5Easy::File file(inputfile, H5Easy::File::ReadWrite);

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
    // file.getGroup("osm").createDataSet("polygons", ds,
    //                                    HighFive::AtomicType<double>(), props);
    // file.getGroup("osm").createDataSet("polygons_idx", ds,
    //                                    HighFive::AtomicType<uint32_t>(), props);
  }

  // open created datasets
  HighFive::DataSet linestrings_ds = file.getDataSet("/osm/linestrings");
  HighFive::DataSet linestrings_idx = file.getDataSet("/osm/linestrings_idx");

  IndirectionAppender<double, 2> emit_linestring(linestrings_ds,
                                                 linestrings_idx);

  // HighFive::DataSet polygons_ds = file.getDataSet("/osm/polygons");
  // HighFive::DataSet polygons_idx = file.getDataSet("/osm/polygons_idx");

  // IndirectionAppender<double, 2> emit_polygon(polygons_ds, polygons_idx);

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

    // assemble coordinates
    Linestring linestring;
    for (const auto &e : elems) {
      auto row = osm2row[e];
      Point pointdata;
      nodes_coords.select({row, 0}, {1, 2}).read(pointdata);
      // TODO: Assemble a linestring WKB either immediately or with some help of
      // libs Linestrings are modeled as an indirection of points. That is,
      // there are two tables linestring_points and linestring_indices to be
      // written.
      linestring.push_back({pointdata[0], pointdata[1]});
    }

    // fetch way tags
    std::vector<std::string> attr;
    ways_attr.select({i, 0}, {1, 1}).read(attr);

    // deserialize tags
    picojson::value v;
    std::string err = picojson::parse(v, attr[0]);
    if (!err.empty()) {
      std::cerr << err << std::endl;
    }

    // check for area feature
    bool is_area =
        std::any_of(AREA_KEYS.begin(), AREA_KEYS.end(),
                    [&v](auto &key) { return v.contains(key); }) ||
        std::any_of(AREA_TAGS.begin(), AREA_TAGS.end(),
                    [&v](const auto &tag) {
                      return std::find(tag.second.begin(), tag.second.end(),
                                       v.get(tag.first).to_str()) !=
                             tag.second.end();
                    }) ||
        std::any_of(AREA_TAGS_NOT.begin(), AREA_TAGS_NOT.end(),
                    [&v](const auto &tag) {
                      return v.contains(tag.first) &&
                             !(std::find(tag.second.begin(), tag.second.end(),
                                         v.get(tag.first).to_str()) !=
                               tag.second.end());
                    });

    // load linestrings
    if (is_area && linestring.front() == linestring.back()) {
      // TODO: triangulate, create and fill triangle table, keep track of
      // indices (map table) emit_polygon(linestring);
      continue;
    }

    emit_linestring(linestring);

#ifdef DEBUG_TRUNCATE
    // Debug TRuncate will run this operation, but only to 1% of the input
    if ((double)i / (double)n_ways > 0.01)
      break;
#endif
    if (i % 100 == 0)
      std::cout << "Progress: " << (double)i / (double)n_ways << "\r";
    std::cout.flush();
  }
}

void _resolve_osm_relations(std::string inputfile) {
  std::cout << "Resolving relations..." << std::endl;
  H5Easy::File file(inputfile, H5Easy::File::ReadWrite);

  // load linestring indices
  auto ways = H5Easy::load<std::vector<uint64_t>>(file, "/osm/ways");
  std::cout << "Way count: " << ways.size() << std::endl;

  std::map<uint64_t, uint64_t> osm2row;
  for (size_t i = 0; i < ways.size(); i++)
    osm2row[ways[i]] = i;
  ways.clear();

  // create datasets
  if (!file.getGroup("osm").exist("parts")) {
    HighFive::DataSpace ds =
        HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED, 2});
    HighFive::DataSetCreateProps props;
    props.add(HighFive::Chunking(std::vector<hsize_t>{1024 * 1024, 2}));
    props.add(HighFive::Deflate(9));

    // create the triangle datasets (triangle and trin_idx)
    // TRIANGLE TABLE*
    file.getGroup("osm").createDataSet("triangles", ds,
                                       HighFive::AtomicType<double>(), props);
    file.getGroup("osm").createDataSet("triangles_idx", ds,
                                       HighFive::AtomicType<uint32_t>(), props);

    // TODO: create mapping table (between polygon and triangles),is this
    // mapping_idx just a colomn? MAPPING TABLE*
    file.getGroup("osm").createDataSet("mapping_idx", ds,
                                       HighFive::AtomicType<double>(), props);
  }

  // open triangle dataset
  // create indirection Appender for triangles
  HighFive::DataSet triangles_ds = file.getDataSet("/osm/triangles");
  HighFive::DataSet triangles_idx = file.getDataSet("/osm/triangles_idx");

  IndirectionAppender<double, 2> emit_triangles(triangles_ds, triangles_idx);

  // open mapping (between polygon and triangles) dataset
  HighFive::DataSet mapping_idx = file.getDataSet("/osm/...");

  // process relations
  size_t n_relations = H5Easy::getSize(file, "/osm/relations");
  std::cout << "Relation count: " << n_relations << std::endl;

  HighFive::DataSet relations_refs = file.getDataSet("/osm/relations_refs");
  HighFive::DataSet relations_attr = file.getDataSet("/osm/relations_attr");

  HighFive::DataSetAccessProps aprops;
  aprops.add(HighFive::Caching(512, 64 * 1024 * 1024, 0.5));
  HighFive::DataSet linestrings = file.getDataSet("/osm/linestrings", aprops);
  // H5Pset_chunk_cache( pid, 100, 10000, 0.5)

  for (size_t i = 0; i < n_relations; i++) {
    // fetch relation tags
    std::vector<std::string> attr;
    relations_attr.select({i, 0}, {1, 1}).read(attr);

    // deserialize tags
    picojson::value tags;
    auto err = picojson::parse(tags, attr[0]);
    if (!err.empty())
      std::cerr << err << std::endl;

    // process only type=multipolygon
    if (!tags.contains("type") || tags.get("type").to_str() != "multipolygon") {
      continue;
    }

    // fetch refs (members)
    std::vector<std::string> refs;
    relations_refs.select({i, 0}, {1, 1}).read(refs);

    picojson::value members;
    err = picojson::parse(members, refs[0]);
    if (!err.empty())
      std::cerr << err << std::endl;

    // assemble linestrings
    Polygon polygon;
    for (const auto &m : members.get<picojson::array>()) {
      // only process well formed members
      auto role = m.get("role").get<std::string>();
      if (!(role == "outer" || role == "inner"))
        continue;

      auto row = osm2row[(size_t)m.get("member_id").get<double>()];
      Linestring linestringdata;
      linestrings.select({row, 0}, {1, 1}).read(linestringdata);
      // TODO: Assemble a linestring WKB either immediately or with some help of
      // libs Lines_resolve_osm_relationstrings are modeled as an indirection of
      // points. That is, there are two tables linestring_points and
      // linestring_indices to be written.
      polygon.push_back(linestringdata);
    }

    // TODO: compose and triangulate
    auto indices = triangulation::earcut(polygon);
    // flatten points of polygon
    std::vector<Point> points;
    for (auto const &ls : polygon) {
      points.insert(points.end(), ls.begin(), ls.end());
    }

    // assemble triangles
    std::vector<std::vector<Point>> triangles;
    for (size_t i = 0; i < indices.size() / 3; i++) {
      std::vector<Point> triangle;
      std::cout << "Triangle [";
      for (auto j = 0; j < 3; j++) {
        triangle.push_back(points[i * 3 + j]);
        std::cout << "[" << points[i * 3 + j][0] << ", " << points[i * 3 + j][1]
                  << "]";
      }
      std::cout << " ]" << std::endl;
      break;

      triangles.push_back(triangle);
    }

    // TODO: write to trinagles table in h5

    // TODO: load triangles
    // firstly show the result of earcut, figure the format of results out
    // emit_triangles(tri_linestrings)

#ifdef DEBUG_TRUNCATE
    // Debug TRuncate will run this operation, but only to 1% of the input
    if ((double)i / (double)n_ways > 0.01)
      break;
#endif
    if (i % 100 == 0)
      std::cout << "Progress: " << (double)i / (double)n_relations << "\r";
    std::cout.flush();
  }
}

bool resolve_osm_geometry(std::string inputfile, std::string output) {
  _resolve_osm_ways(inputfile);
  // _resolve_osm_relations(inputfile);

  return true;
}
