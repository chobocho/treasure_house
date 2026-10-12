// geom 을 가져다 쓰는 크레이트
use geom::square;

fn main() {
    println!("{}", square!(4));
    // use 없이 경로로 불러도 된다.
    println!("{}", geom::square!(2 + 3));
}
