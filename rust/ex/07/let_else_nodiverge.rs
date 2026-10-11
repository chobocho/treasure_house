fn main() {
    let input = "x";
    let Ok(n) = input.parse::<i32>() else {
        println!("숫자가 아니다");
    };
    println!("{n}");
}
//@ expect: E0308
