#ifndef OSM_RESOLVEGEOM
#define OSM_RESOLVGEOM

bool resolve_osm_geometry(std::string inputfile, std::string output,
                          std::string method, std::string nodes_query=".",std::string ways_query=".",std::string relations_query=".");

#endif
