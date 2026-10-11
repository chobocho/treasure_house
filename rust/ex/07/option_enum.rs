// 표준 라이브러리의 Option 은 평범한 열거형이다:
//     enum Option<T> { None, Some(T) }
fn find(names: &[&str], target: &str) -> Option<usize> {
    for (i, n) in names.iter().enumerate() {
        if *n == target {
            return Some(i);
        }
    }
    None
}

fn main() {
    let names = ["kim", "lee"];
    for who in ["lee", "park"] {
        match find(&names, who) {
            Some(i) => println!("{who}: {i}번"),
            None => println!("{who}: 없음"),
        }
    }
}
