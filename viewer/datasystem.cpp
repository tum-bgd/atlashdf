#include<vector>
#include<stdint.h>

#include<highfive/H5Easy.hpp>
#include<iostream>

#include "datasystem.h"



bool DataSystem::Load(std::string filename)
{
	std::cout << "Loading linestrings from " << filename << std::endl;
	H5Easy::File file(filename, H5Easy::File::ReadOnly);
	try{
        index = H5Easy::load<index_type>(file, "/osm/ways_triangles_idx"); // can be linestring_idx or param @TODO
        coords = H5Easy::load<coord_type>(file, "/osm/ways_triangles");
	}catch(...)
	{
	    std::cout << "Loading failed. Expected /osm/ways_triangles_idx and /osm/ways_triangles" << std::endl;
	    clear();
	    return false;
	}
	std::cout << "Found " << index.size() << "linestrings with a total of " << coords.size() << "points" << std::endl;
	return true;
}


std::vector<double> DataSystem::getMBR()
{
   double minX = std::numeric_limits<double>::infinity();
   double maxX = -std::numeric_limits<double>::infinity();
   double minY = std::numeric_limits<double>::infinity();
   double maxY = -std::numeric_limits<double>::infinity();
   for (const auto &p: coords)
   {
	if (p[0] < minX) minX = p[0];
	if (p[0] > maxX) maxX = p[0];
	if (p[1] < minY) minY = p[1];
	if (p[1] > maxY) maxY = p[1];
   }
   return {minX, maxX, minY, maxY};
}
