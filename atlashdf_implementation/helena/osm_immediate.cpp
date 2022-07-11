#include<iostream>
#include "osm_immediate.h"

#include "libs/osmpbfreader.h"
#include "libs/picojson.h"
using namespace osmpbfreader;

#include "atlashdftools.h"

// from osmpbfreader.h
//typedef std::map<std::string, std::string> Tags;
//typedef std::vector<std::pair<OSMPBF::Relation::MemberType, uint64_t> > References;

std::string to_json(const Tags &tags)
{
    picojson::object o;
    for (const auto &i: tags)
       o[i.first] = picojson::value(i.second);
    picojson::value v(o);
    std::string json_str = v.serialize();
    return json_str;
}




struct interrupt{};


struct Visitor {
    int N=0;
    atlas::AtlasGroup g;
    atlas::ChunkedOSMImmediateWriter imwriter;
    Visitor(std::string filename, std::string group): g(filename, group), imwriter(g)
    {
	
    }

    void node_callback(uint64_t osmid, double lon, double lat, const Tags &tags){
	imwriter.node(osmid, {lon,lat}, to_json(tags));
	N++;
/*	if (N > 10)
	    throw(interrupt());*/
    }
    void way_callback(uint64_t osmid, const Tags &tags, const std::vector<uint64_t> &refs){}
    void relation_callback(uint64_t osmid, const Tags &tags, const References &refs){}
};

void import_osm_immediate(std::string input, std::string output)
{

    Visitor v (output,"osm");
    try{
	read_osm_pbf(input, v);
    }catch (interrupt i)
    {

    }
}
