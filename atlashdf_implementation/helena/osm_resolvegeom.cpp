#include<iostream>
#include<map>
#include <string>
#include <sstream>
#include <vector>

#include<highfive/H5Easy.hpp>


bool resolve_osm_geometry(std::string inputfile, std::string output)
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
   
    // now we have osm2row with binary search or hash-based access (turn it into a unordered_map) for resolving OSM
    /*while(true)
    {
	uint64_t query;
	std::cout << "> ";
	std::cin >> query;
	std::cout << "Query: " << query << " resolved to " << osm2row[query] << std::endl;
    }*/
    // transform ways
    n_ways = H5Easy::getSize(file, "/osm/ways");
    
    HighFive::DataSet ways_refs = file.getDataSet("/osm/ways_refs");
    HighFive::DataSet nodes_coords = file.getDataSet("/osm/nodes_coords");
    
    std::cout << "Ways: " << n_ways << std::endl;
    for (size_t i=0; i<n_ways; i+= 1024)
    {
	 std::vector<std::string> result;
	 ways_refs.select({i,0}, {1,1}).read(result);
	 
	 std::stringstream ss(result[0]);
	 std::string item;
	 std::vector<uint64_t> elems;
	 while (std::getline(ss, item, ',')) {
	    elems.push_back(std::stoull(item));
	}

	for (const auto &e:elems)
	{
	   auto row = osm2row[e];
	   std::vector<double> pointdata;
	   nodes_coords.select({row,0}, {1,2}).read(pointdata);
	    // TODO: Assemble a linestring WKB either immediately or with some help of libs

	}
	break;
    }

   
    return true;
}
