use std::{fs::File, io::BufReader};

use georaster::geotiff::GeoTiffReader;

fn main() {
    let file = hdf5::File::open("data/oberbayern-water-earcut.h5").unwrap(); // open for reading
    let ds = file.dataset("osm/ways_triangles").unwrap(); // open the dataset
    let data = ds.read_2d::<f64>().unwrap();

    // read image metadata for alignment
    let tiff = File::open("data/oberbayern_S2_10m_subset.tiff").unwrap();
    let tiff = GeoTiffReader::open(BufReader::new(tiff)).unwrap();

    let (width, height) = tiff.image_info().dimensions.unwrap();
    let [offset_x, offset_y] = tiff.origin().unwrap();
    let [pixel_width, pixel_height] = tiff.pixel_size().unwrap();

    // reproject triangles to image CRS
    let from = "EPSG:4326";
    let to = "EPSG:3035";

    let wgs84_to_laea = proj::Proj::new_known_crs(from, to, None).unwrap();

    let vertices: Vec<_> = data
        .rows()
        .into_iter()
        .map(|coord| {
            let result = wgs84_to_laea.convert((coord[0], coord[1])).unwrap();
            [
                ((result.0 - offset_x) / (width as f64 * pixel_width) * 2. - 1.) as f32,
                ((result.1 - offset_y - height as f64 * pixel_height)
                    / (height as f64 * pixel_height.abs())
                    * 2.
                    - 1.) as f32,
            ]
        })
        .collect();

    let mask = atlashdf_rs::mask::Mask::from(width as usize, height as usize, &vertices);

    // display in window
    let width: usize = 800;
    let height: usize = 600;

    let mut win = minifb::Window::new(
        "Triangle",
        width,
        height,
        minifb::WindowOptions {
            scale_mode: minifb::ScaleMode::Stretch,
            ..Default::default()
        },
    )
    .unwrap();
    while win.is_open() {
        win.update_with_buffer(
            &mask.0.iter().map(|c| *c as u32 * 255).collect::<Vec<u32>>(),
            mask.0.ncols(),
            mask.0.nrows(),
        )
        .unwrap();
    }
}
