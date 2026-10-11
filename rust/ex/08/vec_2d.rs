fn main() {
    // 벡터의 벡터 — 줄마다 길이가 달라도 된다.
    let mut grid = vec![vec![0; 3]; 2];
    grid[1][2] = 7;
    grid.push(vec![9]);

    let mut cells = 0;
    for row in &grid {
        println!("{row:?}");
        cells += row.len();
    }
    println!("{cells}칸");
}
