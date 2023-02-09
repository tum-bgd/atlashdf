use std::{fs::File, io::BufReader};

use georaster::geotiff::GeoTiffReader;
use pyo3::prelude::*;

/// Get mask
#[pyfunction]
fn get_mask(py: Python, h5file: String, tiff: String) -> PyResult<&numpy::PyArray2<bool>> {
    let file = hdf5::File::open(h5file).unwrap(); // open for reading
    let ds = file.dataset("osm/ways_triangles").unwrap(); // open the dataset
    let data = ds.read_2d::<f64>().unwrap();

    // read image metadata for alignment
    let tiff = File::open(tiff).unwrap();
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

    let mask = crate::mask::Mask::from(width as usize, height as usize, &vertices);

    let pyarray = numpy::PyArray2::from_array(py, &mask.0);
    Ok(pyarray)
}

/// AtlasHDF Python module implemented in Rust.
#[pymodule]
fn atlashdf_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_mask, m)?)?;
    Ok(())
}
