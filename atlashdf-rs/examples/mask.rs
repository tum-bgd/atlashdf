use std::{fs::File, io::BufReader};

use georaster::geotiff::GeoTiffReader;

fn main() {
    // read image metadata for alignment
    let tiff = File::open("data/Sentinel-2/Oberbayer_10m_3035_4bands.tif").unwrap();
    let tiff = GeoTiffReader::open(BufReader::new(tiff)).unwrap();

    let (width, height) = tiff.image_info().dimensions.unwrap();

    let [offset_x, offset_y] = tiff.origin().unwrap();
    let [pixel_width, pixel_height] = tiff.pixel_size().unwrap();

    let bbox = [
        offset_x,
        offset_y + pixel_height as f64 * height as f64,
        offset_x + pixel_width as f64 * width as f64,
        offset_y,
    ];

    let collections = &["data/oberbayern-water-earcut.h5/osm/ways_triangles"];

    let crs = "EPSG:3035";

    // get maks
    let mask = atlashdf_rs::get_mask(
        width as usize,
        height as usize,
        &bbox,
        crs,
        collections,
        crs,
    );

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
            &mask.iter().map(|c| *c as u32 * 255).collect::<Vec<u32>>(),
            mask.ncols(),
            mask.nrows(),
        )
        .unwrap();
    }
}
