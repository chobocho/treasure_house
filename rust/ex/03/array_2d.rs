use std::any::type_name_of_val;

fn main() {
    // 세 칸짜리 배열을 두 개 담은 배열
    let mut grid = [[1, 2, 3], [4, 5, 6]];
    println!("{}", type_name_of_val(&grid));
    println!("행 {}개, 열 {}개", grid.len(), grid[0].len());
    // [행][열] 차례로 적는다
    println!("둘째 행 셋째 칸 = {}", grid[1][2]);
    grid[0][0] = 10;
    println!("첫째 행 = {:?}", grid[0]);
    println!("{grid:?}");
    // [[값; 열]; 행] — 0 으로 채운 3행 4열
    let board = [[0_u8; 4]; 3];
    println!("{board:?}");
    println!("{}바이트", size_of_val(&board));
}
