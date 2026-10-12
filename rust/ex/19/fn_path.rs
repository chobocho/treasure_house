fn main() {
    let words = ["apple", "fig", "banana"];
    // 메서드도 함수다. 타입 이름을 앞세워 값으로 넘긴다.
    let lens: Vec<usize> =
        words.iter().copied().map(str::len).collect();
    println!("{lens:?}");
    // 인자가 둘인 메서드는 fold 의 둘째 인자 자리에 맞는다.
    let longest = lens.iter().copied().fold(0, usize::max);
    println!("{longest}");

    let owned: Vec<String> =
        words.into_iter().map(String::from).collect();
    println!("{owned:?}");

    let upper: Vec<String> = owned
        .iter()
        .map(String::as_str)
        .map(str::to_uppercase)
        .collect();
    println!("{upper:?}");

    let ops: [(&str, fn(u32, u32) -> u32); 3] =
        [("pow", u32::pow), ("max", u32::max), ("add", |a, b| a + b)];
    for (name, op) in ops {
        println!("{name}(2, 10) = {}", op(2, 10));
    }
}
