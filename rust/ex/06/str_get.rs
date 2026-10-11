fn main() {
    let s = String::from("한글");
    // get 은 패닉하지 않고 Option 으로 답한다
    println!("{:?}", s.get(0..3));
    println!("{:?}", s.get(0..1));
    println!("{:?}", s.get(0..99));
}
