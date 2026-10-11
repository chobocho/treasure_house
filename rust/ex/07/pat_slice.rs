fn describe(xs: &[i32]) -> String {
    match xs {
        [] => String::from("비었다"),
        [one] => format!("하나: {one}"),
        [first, second] => format!("둘: {first}, {second}"),
        // .. 은 "여기에 몇 개든". rest @ .. 로 이름을 붙일 수도 있다.
        [first, .., last] => format!("{first} … {last}"),
    }
}

fn sum(xs: &[i32]) -> i32 {
    match xs {
        [] => 0,
        [head, tail @ ..] => head + sum(tail),
    }
}

fn main() {
    println!("{}", describe(&[]));
    println!("{}", describe(&[7]));
    println!("{}", describe(&[7, 8]));
    println!("{}", describe(&[1, 2, 3, 4]));
    println!("{}", sum(&[1, 2, 3, 4]));
}
