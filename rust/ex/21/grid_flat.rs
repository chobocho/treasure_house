// 줄은 ; 로, 칸은 , 로 나눠 적는 2차원 벡터.
macro_rules! grid {
    ($( $( $x:expr ),+ );+) => {
        vec![ $( $( $x ),+ ),+ ]
    };
}

fn main() {
    let g = grid![1, 2, 3; 4, 5, 6];
    println!("{g:?}");
    println!("{}", g.len());
    // 줄마다 칸 수가 달라도 된다.
    let ragged = grid![1; 2, 3; 4, 5, 6];
    println!("{ragged:?}");
}
