fn main() {
    let team = ["kim", "lee", "park"];

    // cycle — 끝나면 처음부터 다시. take 로 끊는다
    let week: Vec<&str> =
        team.iter().copied().cycle().take(7).collect();
    println!("{week:?}");

    // zip 은 짧은 쪽에서 끝나므로 take 없이도 멈춘다
    let days = ["월", "화", "수", "목", "금"];
    let plan: Vec<String> = days
        .iter()
        .zip(team.iter().cycle())
        .map(|(day, who)| format!("{day}:{who}"))
        .collect();
    println!("{}", plan.join(" "));

    // nth 는 건너뛴 것까지 꺼내 쓴다
    let mut rest = days.iter();
    println!("{:?}", rest.nth(1));
    println!("{:?}", rest.nth(1));
    println!("{:?} {:?}", rest.next(), rest.next());

    // last 는 끝까지 돌고 마지막 것을 준다
    println!("{:?}", days.iter().last());
    // 뒤에서 세려면 뒤집어서 nth
    println!("{:?}", days.iter().rev().nth(1));
}
