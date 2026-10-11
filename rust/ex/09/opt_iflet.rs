fn show(port: Option<u16>) {
    // if let — 있을 때만 블록을 실행한다.
    if let Some(p) = port {
        println!("if let: 포트 {p}");
    }

    // let else — 없으면 빠져나가고, 있으면 p 를 아래에서 계속 쓴다.
    let Some(p) = port else {
        println!("let else: 포트가 없어 돌아간다");
        return;
    };
    println!("let else: 포트 {p}");
}

fn main() {
    show(Some(443));
    show(None);
}
