fn main() {
    let mut temps = [21.5, 19.0, 23.2];
    // 정수 배열이었다면 이 줄로 정렬된다
    temps.sort();
    println!("{temps:?}");
}
//@ expect: E0277
