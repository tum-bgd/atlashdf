#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
// The AtlasHDF module
#include <osm_immediate.h>
//#include <osm_resolvegeom.h>

class AtlasHDF
{
protected:
std::string hdf_container;
int chunk_size = 1024;
public:
  AtlasHDF() :hdf_container(""){}
  AtlasHDF& set_container(std::string filename){
      hdf_container = filename;
      if (false) {
	  FILE *f = fopen(filename.c_str(),"w");
	  if (f == NULL) throw(std::runtime_error("Cannot truncate " + filename));
	  fclose(f);
       }
       return *this; // method chaining by returning a self-reference
  }
  
  AtlasHDF &import(std::string filename)
  {
      if (hdf_container == "")
        throw(std::runtime_error("Run set_container before import"));
      std::cout << "Import called" << std::endl;
      import_osm_immediate(filename,
                           hdf_container,
                           chunk_size);
      return *this;
  }
  

  
};


// -------------
// pure C++ code
// -------------

std::vector<int> multiply(const std::vector<double>& input)
{
  std::vector<int> output(input.size());

  for ( size_t i = 0 ; i < input.size() ; ++i )
    output[i] = 10*static_cast<int>(input[i]);

  return output;
}

// ----------------
// Python interface
// ----------------

namespace py = pybind11;

// wrap C++ function with NumPy array IO
py::array_t<int> py_multiply(py::array_t<double, py::array::c_style | py::array::forcecast> array)
{
  // allocate std::vector (to pass to the C++ function)
  std::vector<double> array_vec(array.size());

  // copy py::array -> std::vector
  std::memcpy(array_vec.data(),array.data(),array.size()*sizeof(double));

  // call pure C++ function
  std::vector<int> result_vec = multiply(array_vec);

  // allocate py::array (to pass the result of the C++ function to Python)
  auto result        = py::array_t<int>(array.size());
  auto result_buffer = result.request();
  int *result_ptr    = (int *) result_buffer.ptr;

  // copy std::vector -> py::array
  std::memcpy(result_ptr,result_vec.data(),result_vec.size()*sizeof(int));

  return result;
  }
   

template<typename vtype>
py::array wrap(vtype v)
{
   return py::array(v.size(),v.data()); // does a copy
}

PYBIND11_MODULE(atlashdf,m)
{
  m.doc() = "atlashdf module";
 py::class_<AtlasHDF>(m, "AtlasHDF")
    .def(py::init<>())
    .def("import_immediate", &AtlasHDF::import)
    .def("set_container", &AtlasHDF::set_container)
    ;


  
//  m.def("multiply", &py_multiply, "Convert all entries of an 1-D NumPy-array to int and multiply by 10");
}


// wrap as Python module
/*PYBIND11_MODULE(spatialfacet,m)
{
  m.doc() = "pybind11 example plugin";

  m.def("multiply", &py_multiply, "Convert all entries of an 1-D NumPy-array to int and multiply by 10");
  m.def("test", &py_multiply, "Convert all entries of an 1-D NumPy-array to int and multiply by 10");
}


PYBIND11_MODULE(spatialfacet,m) {
    py::class_<SpatialFacetMiner>(m, "SpatialFacetMiner")
    .def(py::init<>())
    .def("add_database", &SpatialFacetMiner::add_database)
    .def("query", [](SpatialFacetMiner &m,std::string query_string, int first, int max, int check_at_least){return m.query(query_string,first,max,check_at_least, false);})
    .def("query_with_data", [](SpatialFacetMiner &m,std::string query_string, int first, int max, int check_at_least){return m.query(query_string,first,max,check_at_least, true);})
    .def("getSpyData", [](SpatialFacetMiner &m){
	auto &spy = m.getSpy();
	return py::make_tuple(
	    wrap(spy.coords[0]),
	    wrap(spy.coords[1]),
	    wrap(spy.docids),
	    wrap(spy.weights)
	 );
	 })
   .def("getSpyStringData",[](SpatialFacetMiner &m){
      auto &spy = m.getSpy();
      return py::make_tuple(spy.value1, spy.values);

      })

    .def ("augment",[](SpatialFacetMiner &m, std::string query_string,
		       py::array_t<double, py::array::c_style | py::array::forcecast> documents,
		       int n_terms)
    {
	    std::vector<int> stl_documents;
	    auto r = documents.unchecked<1>();
	    for (py::ssize_t i =0; i < r.shape(0); i++)
	      stl_documents.push_back(r(i));
	    
	    std::vector<string> terms; std::vector<double> weights; std::string query_out;	    
//    void augment_query_from_documents(std::string query_string, std::vector<int> documents, int n_terms,
//				      std::vector<std::string> &terms, std::vector<double> &weights, std::string &query_out)
	    
	    m.augment_query_from_documents(query_string, stl_documents,n_terms, terms, weights, query_out);
	   return py::make_tuple(terms, weights, query_out);
	    
    });



      ;
    
}
*/
