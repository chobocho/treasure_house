fn main() {
    let v = vec![1, 2, 3];
    v.iter().map(|x| {
        println!("{x} 를 두 배로");
        x * 2
    });
    println!("끝");
}
//@ warnings: show
