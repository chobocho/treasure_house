unsafe fn get_fast(xs: &[i32], i: usize) -> i32 {
    unsafe { *xs.get_unchecked(i) }
}

fn main() {
    let xs = [10, 20, 30];
    println!("{}", get_fast(&xs, 1));
}
//@ expect: E0133
