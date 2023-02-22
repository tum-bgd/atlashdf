/*
Command line tool for AtlasHDF in the Helena Spatial Big Data Framework
development version / preview
martin.werner@tum.de
License: MIT

*/

#include <argparse.hpp>
#include <iostream>

#include "osm_immediate.h"
#include "osm_resolvegeom.h"

int main(int argc, char **argv) {
  // parse command line arguments
  argparse::ArgumentParser program("atlashdf");
  program.add_argument("-c", "--chunksize")
      .scan<'d', int>()
      .default_value(1024)
      .help("The size of chunks in all dataspaces");
  program.add_argument("-n", "--nodes_query")
      .default_value(std::string("."))
      .help("specify nodes attribute jq filter");
  program.add_argument("-w", "--ways_query")
      .default_value(std::string("."))
      .help("specify ways attribute jq filter");
  program.add_argument("-r", "--relations_query")
      .default_value(std::string("."))
      .help("specify relations attribute jq filter");
  program.add_argument("-r", "--representation")
      .help("representation (schema) to be used")
      .default_value(std::string("immediate"));
  program.add_argument("-t", "--triangulation")
      .help("Triangulation method to be used")
      .default_value(std::string("earcut"))
      .action([](const std::string &value) {
        static const std::vector<std::string> choices = {"earcut", "boost"};
        if (std::find(choices.begin(), choices.end(), value) != choices.end()) {
          return value;
        }
        return std::string("earcut");
      });
  program.add_argument("operation").help("<operation>");
  program.add_argument("input").help("<input>");
  program.add_argument("output")
      .help("<output>")
      .default_value(std::string(""));

  try {
    program.parse_args(argc, argv);
  } catch (const std::runtime_error &err) {
    std::cerr << err.what() << std::endl;
    std::cerr << program;
    return -1;
  } // catch
  // dispatch
  std::string operation = program.get<std::string>("operation");
  if (operation == "import") {
    // for import, we have the following
    auto representation = program.get<std::string>("representation");
    if (representation == "immediate") {
      import_osm_immediate(program.get<std::string>("input"),
                           program.get<std::string>("output"),
                           program.get<int>("chunksize"),
                           program.get<std::string>("nodes_query"),
                           program.get<std::string>("ways_query"),
                           program.get<std::string>("relations_query"));
    }
  } else if (operation == "resolve") {
    resolve_osm_geometry(program.get<std::string>("input"),
                         program.get<std::string>("output"),
                         program.get<std::string>("triangulation"),
                         program.get<std::string>("nodes_query"),
                         program.get<std::string>("ways_query"),
                         program.get<std::string>("relations_query"));

  } else {
    std::cerr << "Your operation is not understood or you did not give "
                 "suitable parameters."
              << std::endl;
    std::cerr << program;
    return -2;
  }

  // everything is fine
  return 0;
}
