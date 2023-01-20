#include<iostream>
#include<vector>
#include<highfive/H5Easy.hpp>


typedef std::vector<std::vector<uint32_t>> index_type;
typedef std::vector<std::vector<double>> coord_type;
    
index_type indices;
coord_type coords;

#define EPS 0.000001

bool near(double x, double y, double u, double v)
{
   return fabs((x-u)*(x-u)+(y-v)*(y-v)) < EPS;
}

size_t find_or_add(double x, double y, std::vector<double> &va)
{
    for (size_t i=0; i<  va.size(); i++)
    {
	if(near(va[i],va[i+1],x,y))
	   return i/2;
        i++; // skip over y
    }
    // not found, add
    va.push_back(x);
    va.push_back(y);
    return (va.size() / 2)-1;
}




void load_opengl(std::string filename, std::vector<double> &vertex_array, std::vector<uint32_t> &index_array)
{
  // This tool prepares vertex array and index array for the tile renderer
    H5Easy::File file(filename, H5Easy::File::ReadOnly);
	try{
        indices = H5Easy::load<index_type>(file, "/osm/ways_triangles_idx"); // can be linestring_idx or param @TODO
        coords = H5Easy::load<coord_type>(file, "/osm/ways_triangles");
	}catch(...)
	{
	    std::cout << "Loading failed. Expected /osm/ways_triangles_idx and /osm/ways_triangles" << std::endl;
	    
	    return;
	}

	std::cout << "Found " << indices.size() << "triangles from ways" <<std::endl;


	
    // Optimizing
    for (auto idx : indices)
     {
	for (auto i=idx[0]; i < idx[1]; i++) // maybe <=?
	{
	    index_array.push_back(
		(uint32_t)find_or_add(coords[i][0],coords[i][1], vertex_array)
	    );
	}
     }
     std::cout << "Compressed Vertices" << vertex_array.size() << std::endl;
     std::cout << "Compressed Indices" << index_array.size() << std::endl;
	
 }

