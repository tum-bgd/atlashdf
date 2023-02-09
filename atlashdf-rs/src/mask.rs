use euc::{rasterizer, DepthStrategy, Pipeline, Target};
use image::ImageResult;
use ndarray::Array2;

struct Triangle;

impl Pipeline for Triangle {
    type Vertex = [f32; 2];
    type VsOut = ();
    type Pixel = bool;

    // Vertex shader
    // - Returns the 3D vertex location, and the VsOut value to be passed to the fragment shader
    #[inline(always)]
    fn vert(&self, pos: &[f32; 2]) -> ([f32; 4], Self::VsOut) {
        ([pos[0], pos[1], 0., 1.], ())
    }

    // Specify the depth buffer strategy used for each draw call
    #[inline(always)]
    fn get_depth_strategy(&self) -> DepthStrategy {
        DepthStrategy::None
    }

    // Fragment shader
    // - Returns (in this case) a boolean
    #[inline(always)]
    fn frag(&self, _: &Self::VsOut) -> Self::Pixel {
        true
    }
}

pub struct Mask(pub Array2<bool>);

impl Target for Mask {
    type Item = bool;

    fn size(&self) -> [usize; 2] {
        [self.0.ncols(), self.0.nrows()]
    }

    unsafe fn set(&mut self, pos: [usize; 2], item: Self::Item) {
        if let Some(p) = self.0.get_mut([pos[1], pos[0]]) {
            *p = item;
        }
    }

    unsafe fn get(&self, pos: [usize; 2]) -> Self::Item {
        *self.0.get([pos[1], pos[0]]).unwrap()
    }

    fn clear(&mut self, fill: Self::Item) {
        self.0.fill(fill);
    }
}

impl Mask {
    pub fn from(width: usize, height: usize, vertices: &[[f32; 2]]) -> Mask {
        let mut mask = Mask(Array2::from_elem([height, width], false));
        Triangle.draw::<rasterizer::Triangles<(f32,)>, _>(vertices, &mut mask, None);
        mask
    }

    /// save mask to image
    pub fn save(&self, path: &str) -> ImageResult<()> {
        let imgbuf: image::ImageBuffer<image::Rgb<u8>, Vec<u8>> =
            image::ImageBuffer::from_fn(self.0.ncols() as u32, self.0.nrows() as u32, |x, y| {
                let v = self.0.get([x as usize, y as usize]).unwrap();
                if *v {
                    image::Rgb([0, 0, 255])
                } else {
                    image::Rgb([0, 0, 0])
                }
            });
        imgbuf.save(path)
    }
}
