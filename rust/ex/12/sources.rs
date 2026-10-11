fn main() {
    // 반복자를 내주는 것들.
    let from_range: Vec<i32> = (1..=3).collect();
    let from_chars: Vec<char> = "가나다".chars().collect();
    let from_lines: Vec<&str> = "첫 줄\n둘째 줄".lines().collect();
    let from_split: Vec<&str> = "a,b,c".split(',').collect();
    println!(
        "{from_range:?}\n{from_chars:?}\n{from_lines:?}\n{from_split:?}"
    );
}
