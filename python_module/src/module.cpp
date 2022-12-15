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
std::string nodes_filter;

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
  AtlasHDF &set_nodes_filter(std::string filter)
  {
    nodes_filter = filter;
    return *this;
  }
  
  AtlasHDF &import(std::string filename)
  {
      if (hdf_container == "")
        throw(std::runtime_error("Run set_container before import"));
      import_osm_immediate(filename,
                           hdf_container,
                           chunk_size, nodes_filter);
      return *this;
  }
  

  
};



// ----------------
// Python interface
// ----------------

namespace py = pybind11;


PYBIND11_MODULE(atlashdf,m)
{
  m.doc() = "atlashdf module";
 py::class_<AtlasHDF>(m, "AtlasHDF")
    .def(py::init<>())
    .def("import_immediate", &AtlasHDF::import)
    .def("set_nodes_filter", &AtlasHDF::set_nodes_filter)
    .def("set_container", &AtlasHDF::set_container)
    ;
}


