#include<vector>
#include<stdint.h>

#include<highfive/H5Easy.hpp>
#include<iostream>

#include "datasystem.h"



bool DataSystem::Load(std::string filename)
{
	std::cout << "Loading linestrings from " << filename << std::endl;
	H5Easy::File file(filename, H5Easy::File::ReadOnly);
	/* not in sync, as streets have to be manually extracted
        index = H5Easy::load<index_type>(file, "/osm/streets_idx"); // can be linestring_idx or param @TODO
        coords = H5Easy::load<coord_type>(file, "/osm/linestrings");
*/
	//@todo: add a try here, because triangles might not be resolved
	auto triangles_idx_tmp = H5Easy::load<index_type>(file, "/osm/triangles_idx"); // can be linestring_idx or param @TODO
        triangles = H5Easy::load<coord_type>(file, "/osm/triangles");
	int warnings;
	for (const auto &t: triangles_idx_tmp)
		{
		    for (int i=t[0]; i < t[1]; i+= 3) // a triangle forward
		    {
			// @todo: hack: there are data problems 0/0 in coordinates
			if (
			    (fabs(triangles[i][0])<0.001 && fabs(triangles[i][1])<0.001) || 
			    (fabs(triangles[i+1][0])<0.001 && fabs(triangles[i+1][1])<0.001) || 
			    (fabs(triangles[i+2][0])<0.001 && fabs(triangles[i+2][1])<0.001)
			    )
			    {
			    warnings ++;
			    #ifdef SHOW_ZEROPOINT_WRONG_TRIANGLES
			    triangles_idx.push_back(t);
			    #endif
			    }else{
			    
			    triangles_idx.push_back(t);
			    
			    }
			    }
			    }
	std::cout << "Found " << triangles_idx.size() / 3 << "good triangles, but rejected " << warnings << " triangles with a 0/0 point" << std::endl;
			
	return true;
}


std::vector<double> DataSystem::getMBR()
{
   double minX = std::numeric_limits<double>::infinity();
   double maxX = -std::numeric_limits<double>::infinity();
   double minY = std::numeric_limits<double>::infinity();
   double maxY = -std::numeric_limits<double>::infinity();
   for (const auto &p: triangles)
   {
       if (fabs(p[0]) <0.001 && fabs(p[1]) < 0.001) continue; // ignore 0 in MBR
	if (p[0] < minX) minX = p[0];
	if (p[0] > maxX) maxX = p[0];
	if (p[1] < minY) minY = p[1];
	if (p[1] > maxY) maxY = p[1];
   }
   return {minX, maxX, minY, maxY};
}
