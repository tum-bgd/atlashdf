#ifndef DATASYSTEM_INC
#define DATASYSTEM_INC

struct DataSystem
{
    // encapsulates our data
    typedef std::vector<std::vector<uint32_t>> index_type;
    typedef std::vector<std::vector<double>> coord_type;
    
    index_type index;
    coord_type coords;
    bool Load(std::string filename);
    void clear(void){  index.clear(); coords.clear();}
    std::vector<double> getMBR();
};

#endif
