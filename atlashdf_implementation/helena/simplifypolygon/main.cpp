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


#include <iostream>
#include <list>

#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point_xy.hpp>
#include <boost/geometry/geometries/polygon.hpp>
#include <boost/geometry/io/wkt/wkt.hpp>

#include <boost/foreach.hpp>


template<typename polygontype>
std::list<polygontype> simpler(const polygontype &poly)
{
    // create a copy of the polygon using only the inner ring
    polygontype master ;
    master.outer() = poly.outer();
    std::cout << boost::geometry::wkt(master) << std::endl;
    std::list<polygontype> current {master};
    // the following loop removes inner_rings from each of current (which is growing for each ring)
    for (const auto &inner_ring :poly.inners())
    {
	std::list<polygontype> next;
	for (auto it = current.begin(); it != current.end(); it++ )
	{
	    std::list<polygontype> result {};
	    boost::geometry::difference(*it, inner_ring, result);
	    next.insert(next.end(), result.begin(), result.end());
	}
	current = next;
	for (const auto &p: current)
	  std::cout << boost::geometry::wkt(p) << std::endl;

    }
    return current;

}



int main()
{
    typedef boost::geometry::model::polygon<boost::geometry::model::d2::point_xy<double> > polygon;

    polygon green, blue;

    boost::geometry::read_wkt(
        "POLYGON((2 1.3,2.4 1.7,2.8 1.8,3.4 1.2,3.7 1.6,3.4 2,4.1 3,5.3 2.6,5.4 1.2,4.9 0.8,2.9 0.7,2 1.3)"
            "(4.0 2.0, 4.2 1.4, 4.8 1.9, 4.4 2.2, 4.0 2.0))", green);
    simpler(green);
    return 0;
	    
    boost::geometry::read_wkt(
        "POLYGON((4.0 -0.5 , 3.5 1.0 , 2.0 1.5 , 3.5 2.0 , 4.0 3.5 , 4.5 2.0 , 6.0 1.5 , 4.5 1.0 , 4.0 -0.5))", blue);

    std::list<polygon> output;
    boost::geometry::difference(green, blue, output);

    int i = 0;
    std::cout << "green - blue:" << std::endl;
    BOOST_FOREACH(polygon const& p, output)
    {
        std::cout << i++ << ": " << boost::geometry::area(p) << std::endl;
    }


    output.clear();
    boost::geometry::difference(blue, green, output);

    i = 0;
    std::cout << "blue - green:" << std::endl;
    BOOST_FOREACH(polygon const& p, output)
    {
        std::cout << i++ << ": " << boost::geometry::area(p) << std::endl;
    }


    return 0;
}
