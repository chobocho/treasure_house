// R 행 C 열. 행과 열의 수가 타입에 적힌다.
struct Matrix<const R: usize, const C: usize> {
    cells: [[i32; C]; R],
}

impl<const R: usize, const C: usize> Matrix<R, C> {
    // 왼쪽의 열 수와 오른쪽의 행 수가 같은 이름 C 다.
    fn mul<const K: usize>(&self, rhs: &Matrix<C, K>) -> Matrix<R, K> {
        let mut cells = [[0; K]; R];
        for r in 0..R {
            for k in 0..K {
                for c in 0..C {
                    cells[r][k] += self.cells[r][c] * rhs.cells[c][k];
                }
            }
        }
        Matrix { cells }
    }
}

fn main() {
    // 2 행 3 열과 3 행 2 열
    let a = Matrix {
        cells: [[1, 2, 3], [4, 5, 6]],
    };
    let b = Matrix {
        cells: [[1, 0], [0, 1], [1, 1]],
    };
    let ab = a.mul(&b);
    println!("{:?}", ab.cells);
    let ba = b.mul(&a);
    println!("{:?}", ba.cells);
}
