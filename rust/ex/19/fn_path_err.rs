fn main() {
    let words = ["apple", "fig", "banana"];
    // 클로저 |w| w.len() 대신 메서드의 이름을 넘긴다.
    let lens: Vec<usize> = words.iter().map(str::len).collect();
    println!("{lens:?}");
}
//@ expect: error
