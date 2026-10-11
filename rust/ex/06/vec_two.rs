fn main() {
    let mut v = vec![1, 2, 3];
    let a = &mut v[0];
    let b = &mut v[1];
    *a += 10;
    *b += 20;
    println!("{v:?}");
}
//@ expect: E0499
