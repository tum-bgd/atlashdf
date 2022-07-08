/*

  EXAMPLE osmium_read_with_progress

  Reads the contents of the input file showing a progress bar.

  DEMONSTRATES USE OF:
  * file input
  * ProgressBar utility function

  SIMPLER EXAMPLES you might want to understand first:
  * osmium_read

  LICENSE
  The code in this example file is released into the Public Domain.

*/

#include <iostream> // for std::cerr

// Allow any format of input files (XML, PBF, ...)
#include <osmium/io/any_input.hpp>
#include <osmium/visitor.hpp>
#include<osmium/handler.hpp>

// Get access to isatty utility function and progress bar utility class.
#include <osmium/util/file.hpp>
#include <osmium/util/progress_bar.hpp>


#include <highfive/H5DataSet.hpp>
#include <highfive/H5DataSpace.hpp>
#include <highfive/H5File.hpp>
// core examplehttps://github.com/BlueBrain/HighFive/blob/master/src/examples/create_extensible_dataset.cpp


using namespace HighFive;
class ChunkedAtlasWriter
{
    private:
    
    HighFive::File file;
    public:
    

    ChunkedAtlasWriter(const std::string filename): file(filename, File::ReadWrite | File::Create | File::Truncate)
    {
            DataSpace dataspace = DataSpace({0, 2}, {DataSpace::UNLIMITED,2});
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
	    static DataSet ds = file.getDataSet("coords"); // static is essential: local statics have one init
	    auto size = ds.getDimensions();
	    auto start_row = size[0];
	    
	    size[0] +=coord_cache.size();
	    ds.resize(size);
	    ds.select({start_row,0},{coord_cache.size() ,2}).write(coord_cache);
	    //std::cout << "DEBUG: coord_cache line 1: " << coord_cache[0][0] << ";" << coord_cache[0][1] << std::endl;
	    coord_cache.clear();

    }
    

};





class AtlasHandler  : public osmium::handler::Handler{
   public:
	int nodes=0;
	int ways = 0;
	int relations = 0;
	ChunkedAtlasWriter writer;

    AtlasHandler (std::string outfile): writer(outfile){};
	

    // The callback functions can be either static or not depending on whether
    // you need to access any member variables of the handler.
     void node(const osmium::Node& node) {
	nodes++;
	const auto l = node.location();
	writer.emit(node.id(), l.lon(), l.lat());
	
        // Getting a tag value can be expensive, because a list of tags has
        // to be gone through and each tag has to be checked. So we store the
        // result and reuse it.
   /*     const char* amenity = node.tags()["amenity"];
        if (amenity) {
            print_amenity(amenity, node.tags()["name"], node.location());
        }*/
//	std::cout << "Node: " << node.id() << std::endl;
    }


     void way	(const osmium::Way & way)	
    {
    ways ++;
  //     std::cout << "Way: " << way.id() << std::endl;
    }
     void relation	(const osmium::Relation & relation)	
    {
    relations ++;
//	   std::cout << "Relation: " << relation.id() << std::endl;
    }

    

}; // class Hanlder




int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " OSMFILE OUTFILE.h5\n";
        return 1;
    }

    AtlasHandler handler(argv[2]);

    try {
        // The Reader is initialized here with an osmium::io::File, but could
        // also be directly initialized with a file name.
        osmium::io::File input_file{argv[1]};
        osmium::io::Reader reader{input_file};

        // Initialize progress bar, enable it only if STDERR is a TTY.
        osmium::ProgressBar progress{reader.file_size(), osmium::isatty(2)};

        // OSM data comes in buffers, read until there are no more.
        while (osmium::memory::Buffer buffer = reader.read()) {
	    osmium::apply(buffer, handler);

/*          for (const auto& object : buffer.select<osmium::OSMObject>()) {
		  
                if (osmium::tags::match_any_of(object.tags(), filter1) &&
                    osmium::tags::match_any_of(object.tags(), filter2)) {
                    writer(object);
                }
	        if (!object.is_compatible_to(osmium::item_type::node))
		   		    std::cout << " no node " << object.id() << std::endl;
		   
            }
*/

	    // Update progress bar for each buffer.



	    
            progress.update(reader.offset());
        }
	handler.writer.flush();

        // Progress bar is done.
        progress.done();

        // You do not have to close the Reader explicitly, but because the
        // destructor can't throw, you will not see any errors otherwise.
        reader.close();
    } catch (const std::exception& e) {
        // All exceptions used by the Osmium library derive from std::exception.
        std::cerr << e.what() << '\n';
        return 1;
    }

    std::cout << handler.nodes << ";" << handler.ways << ";" << handler.relations << "==" <<
                 handler.nodes+handler.ways+handler.relations << std::endl;
 }

