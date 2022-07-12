#ifndef ATLASHDFTOOLS_H_INC
#define ATLASHDFTOOLS_H_INC

#include <highfive/H5DataSet.hpp>
#include <highfive/H5DataSpace.hpp>
#include <highfive/H5File.hpp>

namespace atlas
{

    template<typename group_or_file, typename array_type>
    void flush_array(group_or_file f, std::string dataset_name, array_type &a, unsigned num_columns = 1)
    {
	if (a.size() == 0) // for an empty array, we can't do anything
	  return;
       HighFive::DataSet ds = f.getDataSet(dataset_name);
	auto size = ds.getDimensions();
	auto start_row = size[0];
	size[0] += a.size();
	ds.resize(size);
	ds.select({start_row, 0}, {a.size(), num_columns}).write(a); // note that a is not empty here 
    }



struct AtlasGroup
{
   HighFive::File f;
   std::string group_name;
   
   HighFive::Group g(){
	return f.getGroup(group_name);
   };
   AtlasGroup(std::string filename, std::string group, unsigned flags = HighFive::File::ReadWrite | HighFive::File::Create | HighFive::File::Truncate): f(filename, flags), group_name(group)
	{
	    // if an object group does not exist, create it as a group
	    if (! f.exist(group)){
	       f.createGroup(group);
	    }
	
	    // if the group can't be opened, it is most likely a dataset
	    try {
		g();
	    }catch (HighFive::GroupException &e)
	    {
		throw(std::runtime_error("Group cannot be opened, but a node exists. Might be a conflicting name of a DataSpace"));
	    }
	}


	HighFive::Group  operator() (void){ return g();} ; 
};



struct ChunkedOSMImmediateWriter
{
    AtlasGroup g;
    const size_t blocksize=1*1024*1024; // 1 MB cache per type 
    ChunkedOSMImmediateWriter(AtlasGroup &_g): g(_g){
	// check or create dataspaces
	std::cout << "ChunkedOSMImmediateWriter" << std::endl;
	// here, we just make sure the schema tables exist. The workers will allocate on them
	if (!g().exist("nodes"))
	{
	    HighFive::DataSpace dataspace = HighFive::DataSpace({0, 1}, {HighFive::DataSpace::UNLIMITED,1});
	    HighFive::DataSetCreateProps props;
	    props.add(HighFive::Chunking(std::vector<hsize_t>{1024, 1}));
	    props.add(HighFive::Deflate(9));
	    HighFive::DataSpace coord_ds = HighFive::DataSpace({0, 2}, {HighFive::DataSpace::UNLIMITED,2});
	    HighFive::DataSetCreateProps coord_props;
	    coord_props.add(HighFive::Chunking(std::vector<hsize_t>{1024, 2}));
	    coord_props.add(HighFive::Deflate(9));
	   // Create the dataset
	   g().createDataSet("nodes", dataspace, HighFive::AtomicType<uint64_t>(), props);  
	   g().createDataSet("nodes_coords", coord_ds, HighFive::AtomicType<double>(), coord_props);  
	   g().createDataSet("nodes_attr", dataspace, HighFive::AtomicType<std::string>(), props);  
	   g().createDataSet("ways", dataspace, HighFive::AtomicType<uint64_t>(), props);  
	   g().createDataSet("ways_attr", dataspace, HighFive::AtomicType<std::string>(), props);  
	   g().createDataSet("ways_refs", dataspace, HighFive::AtomicType<std::string>(), props);  
	   g().createDataSet("relations", dataspace, HighFive::AtomicType<uint64_t>(), props);  
	   g().createDataSet("relations_attr", dataspace, HighFive::AtomicType<std::string>(), props);  
	   g().createDataSet("relations_refs", dataspace, HighFive::AtomicType<std::string>(), props);  
	   }
    };

    ~ChunkedOSMImmediateWriter(){
	flush_nodes(); // write all nodes to disk
	flush_ways();
	flush_rels();
    }
    std::vector<std::vector<double>> coord_cache;
    std::vector<std::string> node_attribs;
    std::vector<uint64_t> node_ids;
    void node(uint64_t id, std::vector<double> coords, std::string attrib)
    {
	if (coord_cache.size() > blocksize) {
	  flush_nodes();
	}
	node_ids.push_back(id);
	coord_cache.push_back(coords);
	node_attribs.push_back(attrib);
    }
    std::vector<uint64_t> way_ids;
    std::vector<std::string> way_refs;
    std::vector<std::string> way_attribs;
    
    void way (uint64_t id, std::string refs, std::string attrib)
    {
	if (way_ids.size() > blocksize)
	   flush_ways();
	way_ids.push_back(id);
	way_attribs.push_back(attrib);
	way_refs.push_back(refs);
    }
    std::vector<uint64_t> rel_ids;
    std::vector<std::string> rel_refs;
    std::vector<std::string> rel_attribs;

    void relation (uint64_t id, std::string refs, std::string attrib)
    {
	if (rel_ids.size() > blocksize)
	   flush_rels();
	rel_ids.push_back(id);
	rel_attribs.push_back(attrib);
	rel_refs.push_back(refs);
    }

    
    void flush_nodes()
    {
	flush_array(g(),"nodes_coords",coord_cache,2); // last param is #cols in hdf5
	coord_cache.clear();
	flush_array(g(),"nodes_attr",node_attribs,1); // last param is #cols in hdf5
	node_attribs.clear();
	flush_array(g(),"nodes",node_ids,1); // last param is #cols in hdf5
	node_ids.clear();
    }
    void flush_ways()
    {
	 flush_array(g(),"ways",way_ids,1);
	 flush_array(g(), "ways_refs",way_refs,1);
	 flush_array(g(), "ways_attr", way_attribs,1);
	 way_ids.clear();
	 way_refs.clear();
	 way_attribs.clear();
    
    }


    void flush_rels(){
	flush_array(g(),"relations",rel_ids,1);
	flush_array(g(),"relations_attr",rel_attribs,1);
	flush_array(g(),"relations_refs",rel_refs,1);
	rel_ids.clear();
	rel_refs.clear();
	rel_attribs.clear();
	
    }
    
};



} // namespace
#endif
