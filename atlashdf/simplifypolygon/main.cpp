/*

Proof of Concept for Polygon Simplification

During modeling polygons are often modeled as polygons with holes given as one outer ring and possibly
multiple inner rings (see simple feature specs). For most upstream users of OSM this is not advantageous as
the OSM data model typically foresees tags on the polygon level and less for the individual rings or
parts thereof.

This source code shows how to use the difference algoritm to turn a polygon with inner rings into a
set of polygons. This is advantageous for indexing, as the MBR gets more expressive and - in general -
the data is cast into a set of polygons each of which have no inner rings.

Polygon attributes are replicated to each of those, this could be optimized by indirection.

*/

#include <fstream>
#include <iostream>
#include <list>

#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/geometry/io/wkt/wkt.hpp>

#include <boost/polygon/polygon.hpp>
#include <boost/polygon/voronoi.hpp>

namespace bp = boost::polygon;
namespace bg = boost::geometry;

#include <boost/foreach.hpp>

template <typename polygon, typename polycontainer>
void triangulate(polygon in, polycontainer &out)
{
  /*
  Strategy: Build all cells of Delaunay triangulation and check if they are "within" the polygon
  given. Not fastest, but easiest to implement, hence, errors should be less likely.

  The Voronoi ops are in integer rounded representation, hence, transformation errors do occur.

  Let us see the impact on global scale and maybe try to "re-use" the nearest true coordinate from the input

  */
  // integer rounding for polygon
  namespace trans = boost::geometry::strategy::transform;
  bg::model::box<typename polygon::ring_type::value_type> bounds;
  bg::envelope(in, bounds);
  trans::translate_transformer<double, 2, 2> translate(-bg::get<0>(bounds.min_corner()), -bg::get<1>(bounds.min_corner()));
  trans::translate_transformer<double, 2, 2> backtranslate(bg::get<0>(bounds.min_corner()), bg::get<1>(bounds.min_corner()));
  polygon in2;
  bg::transform(in, in2, translate);
  bg::envelope(in, bounds);
  // slightly less than 32 bit signed range
  double _scale = (double)2147000000 * std::max(bg::get<0>(bounds.max_corner()), bg::get<1>(bounds.max_corner()));

  trans::scale_transformer<double, 2, 2> scale(_scale);
  trans::scale_transformer<double, 2, 2> invscale(1 / _scale);
  polygon in3;
  bg::transform(in2, in3, scale);

  using Point = bp::point_data<int32_t>;
  std::vector<Point> vertices;
  for (const auto &p : in3.outer())
    vertices.push_back({static_cast<int32_t>(bg::get<0>(p)), static_cast<int32_t>(bg::get<1>(p))});
  for (const auto &inner_ring : in3.inners())
    for (const auto &p : inner_ring)
      vertices.push_back({static_cast<int32_t>(bg::get<0>(p)), static_cast<int32_t>(bg::get<1>(p))});

  std::cout << "vertices: " << vertices.size() << std::endl;
  for (const auto p : vertices)
  {

    std::cout << "Using " << p.x() << ";" << p.y() << " as integral coords" << std::endl;
  }
  boost::polygon::voronoi_diagram<double> vd;
  boost::polygon::construct_voronoi(vertices.begin(), vertices.end(), &vd);
  std::cout << "vd.vertices:" << vd.vertices().size() << std::endl;
  for (const auto &vertex : vd.vertices())
  {

    std::vector<Point> triangle;
    auto edge = vertex.incident_edge();
    do
    {
      auto cell = edge->cell();
      assert(cell->contains_point());

      triangle.push_back(vertices[cell->source_index()]);
      if (triangle.size() == 3)
      {
        // process output triangles
        polygon triangle1;

        for (const auto &p : triangle)
        {
          triangle1.outer().push_back({(double)p.x(), (double)p.y()});
        }
        polygon triangle2;
        bg::transform(triangle1, triangle2, invscale);
        bg::transform(triangle2, triangle1, backtranslate);

        // hack: check on centroid. This is a bit safer in degenerate cases
        typename polygon::ring_type::value_type c;
        bg::centroid(triangle1, c);
        if (bg::within(c, in))
        {
          out.push_back(triangle1);
          //   std::cout << bg::wkt(triangle1) << std::endl;
        }
        triangle.erase(triangle.begin() + 1);
      }

      edge = edge->rot_next();
    } while (edge != vertex.incident_edge());
  }
}

template <typename polygon, typename polycontainer>
void fracture(const polygon &in, polycontainer &out)
{
  // in follows boost::geometry::model::polygon and out is a container with push_back of those
  // Step 1: Marshalling from boost::geometry to Boost.Polygon
  using SimplePolygon = bp::polygon_data<double>;
  using ComplexPolygon = bp::polygon_with_holes_data<double>;
  using Point = bp::point_data<double>;
  using PolygonSet = bp::polygon_set_data<double>;
  using SimplePolygons = std::vector<bp::polygon_data<double>>;

  using namespace boost::polygon::operators;

  std::vector<Point> points;
  for (const auto &p : in.outer())
  {
    points.push_back({bg::get<0>(p), bg::get<1>(p)});
  }
  ComplexPolygon p;
  bp::set_points(p, points.begin(), points.end());

  // Outer ring is set.
  std::ofstream rings("rings.dat");
  for (const Point &_p : p)
  {
    rings << std::to_string(_p.x()) << " " << std::to_string(_p.y()) << std::endl;
    std::cout << '\t' << std::to_string(_p.x()) << ", " << std::to_string(_p.y())
              << '\n';
  }
  std::vector<SimplePolygon> inner;
  for (const auto &ring : in.inners())
  {
    points.clear();
    for (const auto &p : ring)
      points.push_back({bg::get<0>(p), bg::get<1>(p)});
    SimplePolygon inner_polygon;
    bp::set_points(inner_polygon, points.begin(), points.end());
    inner.push_back(inner_polygon);
  }
  bp::set_holes(p, inner.begin(), inner.end());
  // inner rings have been marshaled, now ComplexPolygon is complete
  PolygonSet complexPolygons;
  complexPolygons += p;

  SimplePolygons simplePolygons;
  complexPolygons.get<SimplePolygons>(simplePolygons);

  std::cout << "Fractured: \n"
            << simplePolygons.size();
  out.clear();
  std::ofstream fractured("fractured.dat");
  for (const auto &poly : simplePolygons)
  {
    polygon op;
    std::cout << "==" << std::endl;
    for (const Point &p : poly)
    {
      op.outer().push_back(typename polygon::ring_type::value_type(p.x(), p.y()));
      fractured << std::to_string(p.x()) << " " << std::to_string(p.y()) << std::endl;

      std::cout << '\t' << std::to_string(p.x()) << ", " << std::to_string(p.y())
                << '\n';
    }
    out.push_back(op);
    fractured << "NaN NaN" << std::endl;
  }
}

int main()
{
  typedef boost::geometry::model::polygon<boost::geometry::model::d2::point_xy<double>> polygon;

  polygon poly;
  // the input data as test 
  boost::geometry::read_wkt("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0),"
                              "(0.25 0.25, 0.25 0.75, 0.75 0.75, 0.75 0.25, 0.25 0.25),"
	                            "(0.9 0.9, 0.9 0.95, 0.95 0.95, 0.95 0.9, 0.9 0.9)"
	                            ")", poly);
  // creat the polygon named by simple 
  std::vector<polygon> simple;
  fracture(poly, simple);

  std::cout << "Simple now contains " << simple.size() << " polygons." << std::endl;
  for (const auto &p : simple)
  {
    std::cout << "\t" << bg::wkt(p) << std::endl;
  }
  simple.clear();
  //apple the triangulate function to our created polygon
  triangulate(poly, simple);
  //created file and write the results in result.wkt
  std::ofstream f;
  f.open("result.wkt");
  for (const auto p : simple) {
    f << bg::wkt(p) ;
  }
  f.close();

  return 0;
}
