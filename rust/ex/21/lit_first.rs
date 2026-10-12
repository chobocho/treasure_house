// 리터럴이면 첫 갈래, 그 밖의 식이면 둘째 갈래로 간다.
macro_rules! kind {
    ($x:literal) => {
        "리터럴"
    };
    ($x:expr) => {
        "식"
    };
}

fn main() {
    println!("5         {}", kind!(5));
    println!("\"hi\"      {}", kind!("hi"));
    println!("-1.5      {}", kind!(-1.5));
    println!("true      {}", kind!(true));
    println!("(5)       {}", kind!((5)));
    println!("5 + 1     {}", kind!(5 + 1));
    println!("i32::MAX  {}", kind!(i32::MAX));
}
