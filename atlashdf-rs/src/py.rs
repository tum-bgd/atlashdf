use pyo3::prelude::*;

/// Proj info
#[pyfunction]
fn proj_info() -> PyResult<String> {
    Ok(format!(
        "{:#?}",
        proj::ProjBuilder::default().lib_info().unwrap()
    ))
}

/// Get boolean mask
#[pyfunction]
fn get_mask(
    py: Python,
    width: usize,
    height: usize,
    bbox: Vec<f64>,
    bbox_crs: String,
    collections: Vec<String>,
    crs: String,
) -> PyResult<&numpy::PyArray2<bool>> {
    let mask = crate::get_mask(
        width,
        height,
        bbox.as_slice(),
        &bbox_crs,
        collections
            .iter()
            .map(|s| s.as_ref())
            .collect::<Vec<&str>>()
            .as_slice(),
        &crs,
    );

    let pyarray = numpy::PyArray2::from_array(py, &mask);
    Ok(pyarray)
}

/// AtlasHDF Python module implemented in Rust.
#[pymodule]
fn atlashdf_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(proj_info, m)?)?;
    m.add_function(wrap_pyfunction!(get_mask, m)?)?;
    Ok(())
}
