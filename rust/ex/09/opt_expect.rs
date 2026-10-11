fn main() {
    let args: Vec<String> = Vec::new();
    // expect 는 죽을 때 남길 말을 받는다 — 기대한 바를 적는다.
    let name = args.first().expect("이름 인자가 하나는 있어야 한다");
    println!("{name}");
}
//@ exit: 101
