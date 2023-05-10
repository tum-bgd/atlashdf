#include "osm_immediate.h"

#include <osmpbfreader.h>
#include <picojson.h>

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>

#include "atlashdftools.h"

using namespace osmpbfreader;

// from osmpbfreader.h
// typedef std::map<std::string, std::string> Tags;
// typedef std::vector<std::pair<OSMPBF::Relation::MemberType, uint64_t> >
// References;

std::string to_json(const Tags &tags) {
  picojson::object o;
  for (const auto &i : tags)
    o[i.first] = picojson::value(i.second);
  picojson::value v(o);
  std::string json_str = v.serialize();
  return json_str;
}

std::string to_json(const std::vector<uint64_t> &refs) {
  std::string s =
      std::accumulate(std::begin(refs), std::end(refs), std::string(),
                      [](std::string &ss, const uint64_t &v) {
                        std::string s = std::to_string(v);
                        return ss.empty() ? s : ss + "," + s;
                      });
  return s;
}

std::string to_json(const References &refs) {
  // a reference is a link to a thing that is node, way, relation and can have a
  // role(string)
  // OSMPBF::Relation_MemberType_NODE = 0,
  // Relation_MemberType_WAY = 1,
  // Relation_MemberType_RELATION = 2
  static std::map<int, std::string> type2string{
      {0, "node"}, {1, "way"}, {2, "relation"}};
  std::string s =
      std::accumulate(std::begin(refs), std::end(refs), std::string(),
                      [](std::string &ss, const Reference &r) {
                        std::stringstream s;
                        s << "{\"type\":";
                        s << std::quoted(type2string[r.member_type]);
                        s << ",\"member_id\":" << r.member_id;
                        s << ",\"role\": ";
                        s << std::quoted(r.role);
                        s << "}";
                        return ss.empty() ? s.str() : ss + "," + s.str();
                      });
  return "[" + s + "]";
}

struct interrupt {}; // only for debug runs where we stop

struct Visitor {
  int N = 0;
  atlas::AtlasGroup g;
  atlas::ChunkedOSMImmediateWriter imwriter;
#ifdef HAVE_JQ
  void set_jq_nodes(std::string s) { imwriter.set_jq_nodes(s); };
  void set_jq_ways(std::string s) { imwriter.set_jq_ways(s); };
  void set_jq_relations(std::string s) { imwriter.set_jq_relations(s); };
#endif
  Visitor(std::string filename, std::string group, size_t chunksize)
      : g(filename, group), imwriter(g, chunksize) {}
  void progress(int bytes_read, int bytes_available) {
    static double last;
    double now = (double)bytes_read / (double)bytes_available;

    if (now - last > 0.1 || bytes_read == bytes_available || bytes_read == 0) {
      std::cout << "10 % Progress found" << now << " which is " << now << "\r";
      std::cout.flush();
      last = now;
      if (bytes_read == bytes_available)
        std::cout << std::endl;
    }
  }
  void node_callback(uint64_t osmid, double lon, double lat, const Tags &tags) {
    imwriter.node(osmid, {lon, lat}, to_json(tags));
    N++;
  }
  void way_callback(uint64_t osmid, const Tags &tags,
                    const std::vector<uint64_t> &refs) {
    imwriter.way(osmid, to_json(refs), to_json(tags));
  }
  void relation_callback(uint64_t osmid, const Tags &tags,
                         const References &refs) {
    imwriter.relation(osmid, to_json(refs), to_json(tags));
  }
};

// WIP: other queries need to be transported.
void import_osm_immediate(std::string input, std::string output,
                          size_t chunksize, std::string nodes_query,
                          std::string ways_query, std::string relations_query) {
  Visitor v(output, "osm", chunksize);
#ifdef HAVE_JQ
  v.set_jq_nodes(nodes_query);
  v.set_jq_ways(ways_query);
  v.set_jq_relations(relations_query);
#endif
  try {
    read_osm_pbf(input, v);
  } catch (interrupt i) {
  }
}
