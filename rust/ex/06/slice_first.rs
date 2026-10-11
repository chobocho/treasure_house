fn main() {
    let v = vec![10, 20, 30];
    let empty: &[i32] = &[];

    println!("{:?} {:?}", v.first(), v.last());
    println!("{:?} {:?}", empty.first(), empty.last());

    // 첫 칸과 나머지로 가른다
    println!("{:?}", v.split_first());
    println!("{:?}", empty.split_first());

    // 범위도 get 으로 물을 수 있다
    println!("{:?} {:?}", v.get(1..3), v.get(1..5));
}
