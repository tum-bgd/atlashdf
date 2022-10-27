#include<iostream>
#include<map>
#include <string>
#include <sstream>
#include <vector>

#include<highfive/H5Easy.hpp>
#define PICOJSON_USE_INT64
#include "libs/picojson.h"
//struct IndirectionAppender(std::string data_name, std::string index_name, std::vector<double> row)


template<typename dtype, int DIM, int CACHE_SIZE=1024*1024*1024>
class IndirectionAppender
{
private:
    HighFive::DataSet &data, &index;
public:
    IndirectionAppender(HighFive::DataSet &_data, HighFive::DataSet &_index): data(_data),index(_index)
    {
    }
    ~IndirectionAppender(){flush();};
    std::vector<std::vector<dtype>> ccache;
    std::vector<std::vector<uint32_t>> icache;
    void flush(){
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

    void operator()(const std::vector<std::vector<dtype>> &row)
    {
	// Warning: row must be contiguous and strictly DIM
	auto start = data.getDimensions()[0] + ccache.size();
	auto end = start + row.size();
	ccache.insert(ccache.end(), row.cbegin(), row.cend());
	icache.push_back({static_cast<uint32_t>(start), static_cast<uint32_t>(end)});
	if (ccache.size() > CACHE_SIZE)
	  flush();
    }
};


void _resolve_osm_linestrings(std::string inputfile)
{

    size_t n_ways;
    H5Easy::File file(inputfile, H5Easy::File::ReadWrite);
    std::cout << "Resolving Geometry" << std::endl;
    // first step is to load indices
    auto nodes = H5Easy::load<std::vector<uint64_t>>(file, "/osm/nodes");
    std::cout << "nodes " << nodes.size() << ";;" << nodes[0] << std::endl;
    std::map<uint64_t, uint64_t> osm2row;
    for (size_t i=0; i < nodes.size(); i++)
       osm2row[nodes[i]] = i;
    nodes.clear();
   
    // transform ways
    n_ways = H5Easy::getSize(file, "/osm/ways");
    
    HighFive::DataSet ways_refs = file.getDataSet("/osm/ways_refs");
    HighFive::DataSetAccessProps aprops;
    aprops.add(HighFive::Caching(512, 64*1024*1024, 0.5)); // set up significant cache
    HighFive::DataSet nodes_coords = file.getDataSet("/osm/nodes_coords", aprops);
    // H5Pset_chunk_cache( pid, 100, 10000, 0.5)


    /// Create the normalized linestring data
    	if (!file.getGroup("osm").exist("linestrings"))
	{
	    HighFive::DataSpace idx_ds = HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED,2});
	    HighFive::DataSetCreateProps props;
	    props.add(HighFive::Chunking(std::vector<hsize_t>{1024*1024, 2}));
	    props.add(HighFive::Deflate(9));
	   
	    HighFive::DataSpace coord_ds = HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED,2});
	    HighFive::DataSetCreateProps coord_props;
	    coord_props.add(HighFive::Chunking(std::vector<hsize_t>{1024*1024, 2}));
	    coord_props.add(HighFive::Deflate(9));
	   // Create the dataset
	   file.getGroup("osm").createDataSet("linestrings", coord_ds, HighFive::AtomicType<double>(), coord_props);
	   file.getGroup("osm").createDataSet("linestrings_idx", idx_ds, HighFive::AtomicType<uint32_t>(), props); 
    }
    // now the datasets are there. We can open them.

    HighFive::DataSet linestrings_ds = file.getDataSet("/osm/linestrings");
    HighFive::DataSet linestrings_idx = file.getDataSet("/osm/linestrings_idx");
    
    IndirectionAppender<double, 2> emit_linestring(linestrings_ds, linestrings_idx);
    
    std::cout << "Ways: " << n_ways << std::endl;
    for (size_t i=0; i<n_ways; i++)
    {
	 std::vector<std::string> result;
	 ways_refs.select({i,0}, {1,1}).read(result);
	 
	 std::stringstream ss(result[0]);
	 std::string item;
	 std::vector<uint64_t> elems;
	 while (std::getline(ss, item, ',')) {
	    elems.push_back(std::stoull(item));
	}
	std::vector<std::vector<double>> the_linestring;
	for (const auto &e:elems)
	{
	   auto row = osm2row[e];
	   std::vector<double> pointdata;
	   nodes_coords.select({row,0}, {1,2}).read(pointdata);
	    // TODO: Assemble a linestring WKB either immediately or with some help of libs
	    // Linestrings are modeled as an indirection of points. That is, there are two tables
	    // linestring_points and linestring_indices to be written.
	  the_linestring.push_back({pointdata[0], pointdata[1]});
	}
	emit_linestring(the_linestring);
#ifdef DEBUG_TRUNCATE
 	// Debug TRuncate will run this operation, but only to 1% of the input
	if((double) i / (double) n_ways > 0.01)
	  break;
#endif
	if (i % 100 == 0)
	    std::cout << "Progress: " << (double) i / (double) n_ways << "\r";
	std::cout.flush();
    }

    

}

void _resolve_osm_polygons(std::string inputfile)
{

    size_t n_rels;
    H5Easy::File file(inputfile, H5Easy::File::ReadWrite);
    std::cout << "Resolving Polygons" << std::endl;
    // first step is to load indices
    auto nodes = H5Easy::load<std::vector<uint64_t>>(file, "/osm/nodes");
    std::cout << "nodes " << nodes.size() << ";;" << nodes[0] << std::endl;
    std::map<uint64_t, uint64_t> node2row;
    for (size_t i=0; i < nodes.size(); i++)
       node2row[nodes[i]] = i;
    nodes.clear();

    auto ways = H5Easy::load<std::vector<uint64_t>>(file, "/osm/ways");
    std::cout << "ways " << ways.size() << ";;" << ways[0] << std::endl;
    std::map<uint64_t, uint64_t> way2row;
    for (size_t i=0; i < nodes.size(); i++)
       way2row[nodes[i]] = i;
    nodes.clear();
    // At this point, way2row and node2raw can map OSM IDs to rows in AtlasHDF
    
    // transform ways
    n_rels = H5Easy::getSize(file, "/osm/relations");
    
    HighFive::DataSet rels_refs = file.getDataSet("/osm/relations_refs");
    HighFive::DataSet rels_attr = file.getDataSet("/osm/relations_attr");
    HighFive::DataSetAccessProps aprops;
    aprops.add(HighFive::Caching(512, 64*1024*1024, 0.5)); // set up significant cache
    HighFive::DataSet nodes_coords = file.getDataSet("/osm/nodes_coords", aprops);
    


    /// Create the normalized linestring data
    	if (!file.getGroup("osm").exist("polygons"))
	{
	    HighFive::DataSpace idx_ds = HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED,2});
	    HighFive::DataSetCreateProps props;
	    props.add(HighFive::Chunking(std::vector<hsize_t>{1024*1024, 2}));
	    props.add(HighFive::Deflate(9));
	   
	    HighFive::DataSpace coord_ds = HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED,2});
	    HighFive::DataSetCreateProps coord_props;
	    coord_props.add(HighFive::Chunking(std::vector<hsize_t>{1024*1024, 2}));
	    coord_props.add(HighFive::Deflate(9));
	   // Create the dataset
	   file.getGroup("osm").createDataSet("polygons", coord_ds, HighFive::AtomicType<double>(), coord_props);
	   file.getGroup("osm").createDataSet("polygons_idx", idx_ds, HighFive::AtomicType<uint32_t>(), props); 
    }
    // now the datasets are there. We can open them.

    HighFive::DataSet polygons_ds = file.getDataSet("/osm/polygons");
    HighFive::DataSet polygons_idx = file.getDataSet("/osm/polygons_idx");
    
    IndirectionAppender<double, 2> emit_simplepolygon(polygons_ds, polygons_idx);
    
    std::cout << "Relations: " << n_rels << std::endl;
    for (size_t i=0; i<n_rels; i++)
    {
	 std::vector<std::string> result;
	 rels_refs.select({i,0}, {1,1}).read(result);
//	 std::cout << result[0] << std::endl;
	 picojson::value v;
	 std::string refs = result[0];
	 rels_attr.select({i,0},{1,1}).read(result);
	 std::string attr = result[0];
	 std::cout << attr << std::endl;
	 // We are only interested in multipolygons (check the wiki, there are boundaries)
	 if (attr.find("\"type\":\"multipolygon\"") ==std::string::npos)
	 {
	    std::cout << "Skipping" << attr << std::endl;
	    continue;
	 }
	 
	std::string err = picojson::parse(v, result[0]);
	if (! err.empty())
	      throw(std::runtime_error("PicoJSON Error: " + err));
	 if (v.is<picojson::array> ())
	 {
	    auto a = v.get<picojson::array>();
	    for (auto member: a)
	    {
		// this will generate picojson errors if the format is wrong. But error checking is not worth it
	        uint64_t member_id = member.get<picojson::object>()["member_id"].get<int64_t> (); // bug: uint64_t 
		std::string type  = member.get<picojson::object>()["type"].get<std::string> (); 
		std::string role  = member.get<picojson::object>()["role"].get<std::string> (); 
		std::cout << type << "=>" << role << std::endl;
		
	       //std::cout << member.serialize() << std::endl;
	    }
	 }
//	 break;
/*	 std::stringstream ss(result[0]);
	 std::string item;
	 std::vector<uint64_t> elems;
	 while (std::getline(ss, item, ',')) {
	    elems.push_back(std::stoull(item));
	}
	std::vector<std::vector<double>> the_linestring;
	for (const auto &e:elems)
	{
	   auto row = osm2row[e];
	   std::vector<double> pointdata;
	   nodes_coords.select({row,0}, {1,2}).read(pointdata);
	    // TODO: Assemble a linestring WKB either immediately or with some help of libs
	    // Linestrings are modeled as an indirection of points. That is, there are two tables
	    // linestring_points and linestring_indices to be written.
	  the_linestring.push_back({pointdata[0], pointdata[1]});
	}
	emit_linestring(the_linestring);*/
#define DEBUG_TRUNCATE
#ifdef DEBUG_TRUNCATE
 	// Debug TRuncate will run this operation, but only to 1% of the input
	if((double) i / (double) n_rels > 0.01)
	  break;
#endif
	if (i % 100 == 0)
	    std::cout << "Progress: " << (double) i / (double) n_rels << "\r";
	std::cout.flush();
    }

    

}



bool resolve_osm_geometry(std::string inputfile, std::string output)
{
//    _resolve_osm_linestrings(inputfile);
       _resolve_osm_polygons(inputfile);
    
    return true;
}
