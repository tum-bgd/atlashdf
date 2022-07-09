#include<iostream>
#include "osm_immediate.h"

#include "osmpbfreader/osmpbfreader.h"

using namespace osmpbfreader;

// from osmpbfreader.h
//typedef std::map<std::string, std::string> Tags;
//typedef std::vector<std::pair<OSMPBF::Relation::MemberType, uint64_t> > References;

struct Visitor {
    void node_callback(uint64_t osmid, double lon, double lat, const Tags &tags){
	std::cout << "Node " << osmid << std::endl;

    }
    void way_callback(uint64_t osmid, const Tags &tags, const std::vector<uint64_t> &refs){}
    void relation_callback(uint64_t osmid, const Tags &tags, const References &refs){}
};

void import_osm_immediate(std::string input, std::string output)
{

    Visitor v;
    read_osm_pbf(input, v);
}
