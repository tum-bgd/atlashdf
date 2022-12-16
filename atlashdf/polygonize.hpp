#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/geometry/multi/geometries/multi_polygon.hpp>

namespace bg = boost::geometry;

using linestring = std::vector<std::vector<double>>;
using linestrings = std::vector<linestring>;

linestrings merge_linestrings(linestrings parts) {
  linestrings merged = {};

  while (!parts.empty()) {
    linestring part = parts[parts.size() - 1];
    parts.pop_back();

    if (part[0] == part[part.size() - 1]) {
      merged.push_back(part);
    } else {
      bool matched = false;
      for (size_t i = 0; i < parts.size(); i++) {
        if (parts[i][0] == part[part.size() - 1]) {
          part.pop_back();
          for (const auto &p : parts[i]) {
            part.push_back(p);
          }
          parts[i] = part;
          matched = true;
          break;
        } else if (parts[i][parts[i].size() - 1] == part[0]) {
          parts[i].pop_back();
          for (const auto &p : part) {
            parts[i].push_back(p);
          }
          matched = true;
          break;
        }
      }

      if (!matched) {
        merged.push_back(part);
      }
    }
  }

  return merged;
}

std::vector<linestrings> polygonize(linestrings outers, linestrings inners) {
  typedef bg::model::d2::point_xy<double> point;
  typedef bg::model::ring<point> ring;
  typedef bg::model::polygon<point> polygon;
  typedef bg::model::multi_polygon<polygon> multipolygon;

  outers = merge_linestrings(outers);

  multipolygon mp;
  for (const auto &outer : outers) {
    polygon p;
    for (const auto &c : outer) {
      p.outer().push_back({c[0], c[1]});
    }
    mp.push_back(p);
  }

  inners = merge_linestrings(inners);

  for (const auto &inner : inners) {
    ring hole;
    for (const auto &c : inner) {
      hole.push_back({c[0], c[1]});
    }

    for (auto &p : mp) {
      if (bg::within(hole, p)) {
        p.inners().push_back(hole);
        break;
      }
    }
  }

  std::vector<linestrings> out;
  for (const auto &p : mp) {
    linestrings rings;
    linestring coords;
    for (const auto &c : p.outer()) {
      coords.push_back({c.x(), c.y()});
    }
    rings.push_back(coords);
    for (const auto &inner : p.inners()) {
      coords.clear();
      for (const auto &c : inner) {
        coords.push_back({c.x(), c.y()});
      }
      rings.push_back(coords);
    }
    out.push_back(rings);
  }

  return out;
}
