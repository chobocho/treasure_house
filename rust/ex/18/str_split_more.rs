fn main() {
    let line = "09:30 warn 디스크가 거의 찼다";

    // splitn — 앞에서 n 조각까지만. 마지막 조각은 남은 것 전부다
    let parts: Vec<&str> = line.splitn(3, ' ').collect();
    println!("{parts:?}");
    println!("{}", line.split(' ').count());

    // split_once 는 첫 구분자에서, rsplit_once 는 마지막 구분자에서
    let file = "backup.tar.gz";
    println!("{:?}", file.split_once('.'));
    println!("{:?}", file.rsplit_once('.'));
    println!("{:?}", "README".rsplit_once('.'));

    // rsplit — 뒤에서부터 쪼갠다
    let path = "home/kim/notes/todo.txt";
    println!("{:?}", path.rsplit('/').next());
    println!("{:?}", path.rsplit('/').collect::<Vec<_>>());

    // 구분자 자리에 클로저 — 숫자가 아닌 글자마다 쪼갠다
    let not_digit = |c: char| !c.is_ascii_digit();
    println!(
        "{:?}",
        "010-1234 5678".split(not_digit).collect::<Vec<_>>()
    );
    // find 와 matches 도 클로저를 받는다
    println!("{:?}", "item42".find(|c: char| c.is_ascii_digit()));
    println!(
        "{}",
        "a1b22c".matches(|c: char| c.is_ascii_digit()).count()
    );

    // trim_start_matches — 앞에 이어진 같은 글자를 모두 뗀다
    println!("{}", "000120".trim_start_matches('0'));
}
