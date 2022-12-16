#include <fstream>
#include <iostream>
#include <list>
#include <ostream>
#include <string>
#include <vector>

#include <boost/foreach.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/geometry/io/wkt/wkt.hpp>
#include <boost/polygon/polygon.hpp>
#include <boost/polygon/voronoi.hpp>

#include <earcut.hpp>

namespace mapbox {
namespace util {

template <> struct nth<0, std::vector<double>> {
  inline static auto get(const std::vector<double> &v) { return v[0]; };
};
template <> struct nth<1, std::vector<double>> {
  inline static auto get(const std::vector<double> &v) { return v[1]; };
};

} // namespace util
} // namespace mapbox

namespace triangulation {

namespace bp = boost::polygon;
namespace bg = boost::geometry;

typedef boost::geometry::model::d2::point_xy<double> point;
typedef boost::geometry::model::polygon<point> polygon;
typedef boost::geometry::model::multi_polygon<polygon> multipolygon;

std::vector<std::vector<double>>
earcut(std::vector<std::vector<std::vector<double>>> polygon) {
  // triangulate
  auto indices = mapbox::earcut<uint32_t>(polygon);

  // flatten coordinates
  std::vector<std::vector<double>> coords;
  for (const auto &ring : polygon) {
    coords.insert(coords.end(), ring.begin(), ring.end());
  }

  // assemple triangle coordinates
  std::vector<std::vector<double>> triangles;
  for (const auto &i : indices) {
    triangles.push_back(coords[i]);
  }

  return triangles;
};

std::vector<std::vector<double>>
martin(std::vector<std::vector<std::vector<double>>> coords) {
  /*
  Strategy: Build all cells of Delaunay triangulation and check if they are
  "within" the polygon given. Not fastest, but easiest to implement, hence,
  errors should be less likely.

  The Voronoi ops are in integer rounded representation, hence, transformation
  errors do occur.

  Let us see the impact on global scale and maybe try to "re-use" the nearest
  true coordinate from the input
  */

  polygon in;
  for (const auto &c : coords[0]) {
    in.outer().push_back({c[0], c[1]});
  }
  for (size_t i = 1; i < coords.size(); i++) {
    bg::model::ring<point> ring;
    for (const auto &p : coords[i])
      ring.push_back({p[0], p[1]});
    in.inners().push_back(ring);
  }
  // integer rounding for polygon
  namespace trans = boost::geometry::strategy::transform;

  bg::model::box<typename polygon::ring_type::value_type> bounds;

  // translate
  bg::envelope(in, bounds);
  double minx = bg::get<0>(bounds.min_corner());
  double miny = bg::get<1>(bounds.min_corner());
  trans::translate_transformer<double, 2, 2> translate(-minx, -miny);
  trans::translate_transformer<double, 2, 2> backtranslate(minx, miny);

  polygon in2;
  bg::transform(in, in2, translate);

  // scale
  bg::envelope(in2, bounds);
  // slightly less than 32 bit signed range
  double scale_factor =
      (double)2147000000 / std::max(bg::get<0>(bounds.max_corner()),
                                    bg::get<1>(bounds.max_corner()));
  trans::scale_transformer<double, 2, 2> scale(scale_factor);
  trans::scale_transformer<double, 2, 2> invscale(1 / scale_factor);

  polygon in3;
  bg::transform(in2, in3, scale);

  // extract vertices
  using Point = bp::point_data<int32_t>;
  std::vector<Point> vertices;
  for (const auto &p : in3.outer())
    vertices.push_back({static_cast<int32_t>(bg::get<0>(p)),
                        static_cast<int32_t>(bg::get<1>(p))});
  for (const auto &inner_ring : in3.inners())
    for (const auto &p : inner_ring)
      vertices.push_back({static_cast<int32_t>(bg::get<0>(p)),
                          static_cast<int32_t>(bg::get<1>(p))});

  // voronoi
  boost::polygon::voronoi_diagram<double> vd;
  boost::polygon::construct_voronoi(vertices.begin(), vertices.end(), &vd);

  // assemble triangles
  std::vector<std::vector<double>> out;

  for (const auto &vertex : vd.vertices()) {

    std::vector<Point> triangle;
    auto edge = vertex.incident_edge();
    do {
      auto cell = edge->cell();
      assert(cell->contains_point());

      triangle.push_back(vertices[cell->source_index()]);
      if (triangle.size() == 3) {
        // process output triangles
        polygon triangle1;

        for (const auto &p : triangle) {
          triangle1.outer().push_back({(double)p.x(), (double)p.y()});
        }
        polygon triangle2;
        bg::transform(triangle1, triangle2, invscale);
        bg::transform(triangle2, triangle1, backtranslate);

        // hack: check on centroid. This is a bit safer in degenerate cases
        typename polygon::ring_type::value_type c;
        bg::centroid(triangle1, c);
        if (bg::within(c, in)) {
          for (const auto &p : triangle1.outer()) {
            out.push_back({p.x(), p.y()});
          }
        }
        triangle.erase(triangle.begin() + 1);
      }

      edge = edge->rot_next();
    } while (edge != vertex.incident_edge());
  }
  return out;
};

} // namespace triangulation
