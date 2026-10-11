// 타입 인자 T 와 값 인자 N 을 함께 받는다.
#[derive(Debug)]
struct Grid<T, const N: usize> {
    cells: [[T; N]; N],
}

impl<T: Copy + Default, const N: usize> Grid<T, N> {
    fn new() -> Self {
        Grid {
            cells: [[T::default(); N]; N],
        }
    }

    fn size(&self) -> usize {
        N * N
    }
}

fn main() {
    let small: Grid<u8, 2> = Grid::new();
    let big: Grid<bool, 8> = Grid::new();
    println!("{small:?} {}", small.size());
    println!("{} {}", big.size(), big.cells[0][0]);
}
