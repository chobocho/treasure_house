fn main() {
    let x = 3;
    // 식을 글자 그대로 문자열로.
    println!("{} = {}", stringify!(x * 2 + 1), x * 2 + 1);
    // 컴파일할 때 이어 붙인다.
    println!("{}", concat!("v", 1, ".", 2));
    // 이 줄의 자리.
    println!("{}:{}", file!(), line!());
    // 조건부 컴파일의 조건을 bool 로.
    println!("{}", cfg!(debug_assertions));
}
