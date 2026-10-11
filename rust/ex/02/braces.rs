fn main() {
    let width = 3;
    let height = 4;
    // 식은 중괄호 밖에서 인자로 넘긴다
    println!("넓이 {}", width * height);
    // 중괄호 글자를 찍으려면 두 번 쓴다
    println!("{{width}} 자리에 {width} 이 들어간다");
    println!("빈 중괄호 {{}} 도 마찬가지");
}
