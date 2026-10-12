fn add<const N: usize>(a: [i32; N], b: [i32; N]) -> [i32; N] {
    let mut out = [0; N];
    for i in 0..N {
        out[i] = a[i] + b[i];
    }
    out
}

fn main() {
    // 세 칸과 두 칸을 더하려 한다.
    let sum = add([1, 2, 3], [10, 20]);
    println!("{sum:?}");
}
//@ expect: E0308
