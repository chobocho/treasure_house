fn main() {
    let names = ["kim", "lee"];

    // for_each — 사슬 끝에서 원소마다 무언가를 한다.
    names
        .iter()
        .map(|n| n.to_uppercase())
        .for_each(|n| println!("{n}"));
}
