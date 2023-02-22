pub mod mask;
mod py;

pub fn get_mask(
    width: usize,
    height: usize,
    bbox: &[f64],
    bbox_crs: &str,
    collections: &[&str],
    crs: &str,
) -> ndarray::Array2<bool> {
    assert_eq!(bbox.len(), 4);

    // read data
    let mut data = ndarray::Array2::default((0, 2));
    for collection in collections {
        let (file, ds) = collection.split_once(".h5/").unwrap();
        let file = hdf5::File::open(format!("{file}.h5")).unwrap();
        let ds = file.dataset(ds).unwrap();
        data.append(ndarray::Axis(0), ds.read_2d::<f64>().unwrap().view())
            .unwrap();
    }

    // reproject bbox
    let pj = proj::Proj::new_known_crs(bbox_crs, crs, None).unwrap();
    let bbox_min = pj.convert((bbox[0], bbox[1])).unwrap();
    let bbox_max = pj.convert((bbox[2], bbox[3])).unwrap();

    // reproject triangles to map CRS
    let from = "EPSG:4326"; // osm
    let wgs84_to_laea = proj::Proj::new_known_crs(from, crs, None).unwrap();

    let vertices: Vec<_> = data
        .rows()
        .into_iter()
        .map(|coord| {
            let result = wgs84_to_laea.convert((coord[0], coord[1])).unwrap();
            [
                ((result.0 - bbox_min.0) / (bbox_max.0 - bbox_min.0) * 2. - 1.) as f32,
                ((result.1 - bbox_min.1) / (bbox_max.1 - bbox_min.1) * 2. - 1.) as f32,
            ]
        })
        .collect();

    let mask = mask::Mask::from(width, height, &vertices);
    mask.0
}
