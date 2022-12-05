#include <highfive/H5DataSet.hpp>
#include <highfive/H5DataSpace.hpp>
#include <highfive/H5File.hpp>
// core example
// https://github.com/BlueBrain/HighFive/blob/master/src/examples/create_extensible_dataset.cpp

using namespace HighFive;
/*template<std::string space="attrib">
class ChunkedStringTable
{
    private:

    HighFive::File file;
    public:

    ChunkedStringTable(const std::string filename, const std::string dsetname,
const std::vector<size_t>& dims, const std::vector<size_t>& maxdims, bool
truncate=true)
    {
        auto flags = File::ReadWrite | File::Create;
        if (truncate) flags |= File::Truncate;
        file = HighFive::File(filename,  flags)
        DataSpace dataspace = DataSpace(dims, maxdims);
        DataSetCreateProps props;
        props.add(Chunking(std::vector<hsize_t>{1024, 2}));

        // Create the dataset
         file.createDataSet("coords", dataspace,
                                             AtomicType<double>(), props);

    }

    ~ChunkedAtlasWriter(){
        flush();
    }
    std::vector<std::vector<double>> coord_cache;
    void emit(uint64_t id, double lon, double lat)
    {
        // emit to atlas HDF point cloud caching in main memory before flushing
        if(coord_cache.size() >1024*16)
        {
        flush();
        }
        coord_cache.push_back({lon,lat});

    }
    void flush()
    {
            static DataSet ds = file.getDataSet("coords"); // static is
essential: local statics have one init auto size = ds.getDimensions(); auto
start_row = size[0];

            size[0] +=coord_cache.size();
            ds.resize(size);
            ds.select({start_row,0},{coord_cache.size() ,2}).write(coord_cache);
            //std::cout << "DEBUG: coord_cache line 1: " << coord_cache[0][0] <<
";" << coord_cache[0][1] << std::endl; coord_cache.clear();

    }


};

*/
