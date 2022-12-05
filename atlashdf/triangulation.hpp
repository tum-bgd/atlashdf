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
std::vector<uint32_t>
earcut(std::vector<std::vector<std::vector<double>>> polygon) {

  return mapbox::earcut<uint32_t>(polygon);
}
} // namespace triangulation
