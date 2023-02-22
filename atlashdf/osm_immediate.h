#include <string>

#ifndef OSM_IMMEDIATE_INC
#define OSM_IMMEDIATE_INC

void import_osm_immediate(std::string input, std::string output,
                          size_t chunksize, std::string nodes_query = ".",
                          std::string ways_query = ".",
                          std::string relations_query = ".");

#endif
