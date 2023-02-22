#include <picojson.h>

#include <map>
#include <string>
#include <vector>

namespace osm {
using key_values_map = std::map<std::string, std::vector<std::string>>;

const std::vector<std::string> AREA_KEYS = {
    "building", "landuse",  "amenity", "shop",        "building:part",
    "boundary", "historic", "place",   "area:highway"};

const key_values_map AREA_TAGS = {
    {"area", {"yes"}},
    {"waterway", {"riverbank"}},
    {"highway", {"rest_area", "services", "platform"}},
    {"railway", {"platform"}},
    {"natural",
     {"water",     "wood",      "scrub",    "wetland", "grassland", "heath",
      "rock",      "bare_rock", "sand",     "beach",   "scree",     "bay",
      "glacier",   "shingle",   "fell",     "reef",    "stone",     "mud",
      "landslide", "sinkhole",  "crevasse", "desert"}},
    {"aeroway", {"aerodrome"}}};

const key_values_map AREA_TAGS_NOT = {
    {"leisure", {"picnic_table", "slipway", "firepit"}}};

const bool matches(picojson::value &tags, std::vector<std::string> keys,
                   key_values_map key_values, key_values_map key_values_not) {
  return std::any_of(keys.begin(), keys.end(),
                     [tags](auto &key) { return tags.contains(key); }) ||
         std::any_of(key_values.begin(), key_values.end(),
                     [tags](const auto &tag) {
                       return std::find(tag.second.begin(), tag.second.end(),
                                        tags.get(tag.first).to_str()) !=
                              tag.second.end();
                     }) ||
         std::any_of(key_values_not.begin(), key_values_not.end(),
                     [tags](const auto &tag) {
                       return tags.contains(tag.first) &&
                              !(std::find(tag.second.begin(), tag.second.end(),
                                          tags.get(tag.first).to_str()) !=
                                tag.second.end());
                     });
}

}  // namespace osm
