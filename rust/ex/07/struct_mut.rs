struct Counter {
    hits: u32,
    label: String,
}

fn main() {
    // 필드 하나만 mut 로 할 수는 없다 — 값 전체가 가변이거나 아니거나.
    let mut c = Counter {
        hits: 0,
        label: String::from("방문"),
    };
    c.hits += 1;
    c.label.push('!');
    println!("{} {}", c.label, c.hits);
}
