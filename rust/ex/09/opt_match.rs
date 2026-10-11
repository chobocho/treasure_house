fn first_even(xs: &[i32]) -> Option<i32> {
    for &x in xs {
        if x % 2 == 0 {
            return Some(x); // 있다
        }
    }
    None // 없다
}

fn main() {
    for list in [&[1, 4, 6][..], &[1, 3][..]] {
        match first_even(list) {
            Some(n) => println!("첫 짝수 {n}"),
            None => println!("짝수 없음"),
        }
    }
}
