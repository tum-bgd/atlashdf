/*
helena command line tool for AtlasHDF in the Helena Spatial Big Data Framework
development version / preview 
martin.werner@tum.de
License: MIT

*/
#include<iostream>
#include "argparse.hpp"
// and the implementations
#include "osm_immediate.h"



int main(int argc, char **argv)
{
   // parse command line arguments
      argparse::ArgumentParser program("helena");
      program.add_argument("-c", "--chunksize")
        .scan<'d', int>()
	.default_value(1024)
	.help("The size of chunks in all dataspaces");

      /*program.add_argument("-f", "--filter")
      .default_value(std::string(""))
      .help("specify filter string");
  program.add_argument("-w", "--add-ways")
      .help("add way nodes")
      .default_value(false)
      .implicit_value(true);*/
      program.add_argument("-r", "--representation")
	  .help("representation (schema) to be used")
	  .default_value(std::string("immediate"));
      program.add_argument("operation").help("<operation>");
      program.add_argument("input").help("<input>");
      program.add_argument("output").help("<output>");

      try {
	program.parse_args(argc, argv);
      } catch (const std::runtime_error &err) {
	std::cerr << err.what() << std::endl;
	std::cerr << program;
        return -1;
      }//catch
   // dispatch
    std::string operation = program.get<std::string> ("operation");
    if (operation == "import")
    {
	// for import, we have the following
	auto representation=program.get<std::string>("representation");
	if (representation == "immediate")
	{
	  import_osm_immediate(program.get<std::string>("input"), program.get<std::string>("output"),
			       program.get<int>("chunksize"));
	}
    }else
    {
	std::cerr << "Your operation is not understood or you did not give suitable parameters." << std::endl;
	std::cerr << program;
	return -2;
    }
    

   
   // everything is fine
   return 0;
}
