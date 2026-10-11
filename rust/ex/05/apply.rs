fn apply_twice(f: fn(i32) -> i32, x: i32) -> i32 {
    f(f(x))
}

fn add_three(x: i32) -> i32 {
    x + 3
}

fn main() {
    println!("{}", apply_twice(add_three, 10));
    println!("{}", apply_twice(i32::abs, -4));
}
