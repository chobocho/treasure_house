fn main() {
    let mut v = vec![1, 2, 3];
    unsafe {
        let a = &mut v;
        let b = &mut v;
        a.push(4);
        b.push(5);
    }
}
//@ expect: E0499
