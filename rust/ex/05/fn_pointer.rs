fn double(x: i32) -> i32 {
    x * 2
}

fn square(x: i32) -> i32 {
    x * x
}

fn main() {
    // 함수 이름은 값이다. 타입은 fn(i32) -> i32.
    let f: fn(i32) -> i32 = double;
    println!("{}", f(10));

    let table = [double, square];
    for g in table {
        println!("{}", g(6));
    }
}
