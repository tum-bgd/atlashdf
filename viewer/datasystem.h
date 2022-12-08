#ifndef DATASYSTEM_INC
#define DATASYSTEM_INC

struct DataSystem
{
    // encapsulates our data
    typedef std::vector<std::vector<uint32_t>> index_type;
    typedef std::vector<std::vector<double>> coord_type;

    // linestring information
    index_type index;
    coord_type coords;
    // triangulation
    index_type triangles_idx;
    coord_type triangles;
    
    bool Load(std::string filename);
    std::vector<double> getMBR();
};

#endif
