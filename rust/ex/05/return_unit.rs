fn record(score: i32) {
    if score < 0 {
        println!("{score}: 점수가 아니다");
        return; // 값 없이 여기서 돌아간다
    }
    println!("{score}: 기록했다");
}

fn main() {
    record(70);
    // 일찍 돌아간 호출이 돌려준 것도 () 다
    let r = record(-5);
    println!("{r:?}");
}
