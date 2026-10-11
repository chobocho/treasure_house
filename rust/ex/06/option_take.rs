// 표가 있으면 꺼내 주고, 자리는 비워 둔다
fn claim(slot: &mut Option<String>) -> Option<String> {
    slot.take()
}

fn main() {
    let mut slot = Some(String::from("ticket"));

    let first = claim(&mut slot);
    println!("{first:?} {slot:?}");

    // 두 번째에는 줄 것이 없다
    let second = claim(&mut slot);
    println!("{second:?} {slot:?}");
}
