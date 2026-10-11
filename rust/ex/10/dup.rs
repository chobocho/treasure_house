// 타입만 다르고 본문은 글자까지 같다.
fn largest_i32(xs: &[i32]) -> i32 {
    let mut best = xs[0];
    for &x in xs {
        if x > best {
            best = x;
        }
    }
    best
}

fn largest_f64(xs: &[f64]) -> f64 {
    let mut best = xs[0];
    for &x in xs {
        if x > best {
            best = x;
        }
    }
    best
}

fn main() {
    println!("{}", largest_i32(&[3, 9, 4]));
    println!("{}", largest_f64(&[1.5, 0.2]));
}
