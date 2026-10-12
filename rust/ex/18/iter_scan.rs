fn main() {
    // 통장에 들어오고 나간 돈
    let moves = [300, -120, 50, -400, 90];

    // fold 는 다 접은 마지막 값 하나만 준다
    println!("{}", moves.iter().fold(0, |acc, x| acc + x));

    // scan — 접어 가는 값을 원소마다 내놓는다
    let balance: Vec<i32> = moves
        .iter()
        .scan(0, |acc, x| {
            *acc += x;
            Some(*acc)
        })
        .collect();
    println!("{balance:?}");

    // 클로저가 None 을 돌려주면 거기서 끝난다
    let safe: Vec<i32> = moves
        .iter()
        .scan(0, |acc, x| {
            *acc += x;
            if *acc >= 0 { Some(*acc) } else { None }
        })
        .collect();
    println!("{safe:?}");

    // reduce — 처음 값 없이 첫 원소에서 시작한다. 그래서 Option 이다
    let longest = ["fig", "banana", "kiwi"]
        .into_iter()
        .reduce(|a, b| if b.len() > a.len() { b } else { a });
    println!("{longest:?}");
    let nothing: [&str; 0] = [];
    println!("{:?}", nothing.into_iter().reduce(|a, _| a));
}
