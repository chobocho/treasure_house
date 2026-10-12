// 두 배열의 길이가 같은 N 이고, 돌려주는 배열도 N 칸이다.
fn add<const N: usize>(a: [i32; N], b: [i32; N]) -> [i32; N] {
    let mut out = [0; N];
    for i in 0..N {
        out[i] = a[i] + b[i];
    }
    out
}

fn main() {
    let sum = add([1, 2, 3], [10, 20, 30]);
    println!("{sum:?}");
    // 길이가 다른 호출에는 N 이 따로 정해진다.
    let pair = add([1, 2], [3, 4]);
    println!("{pair:?} {}", size_of_val(&pair));
}
