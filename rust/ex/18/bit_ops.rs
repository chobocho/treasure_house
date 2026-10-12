fn show(label: &str, bits: u8) {
    println!("{label:<10}{bits:08b}");
}

fn main() {
    // 비트 하나가 요일 하나 — 오른쪽 끝이 월요일
    let kim: u8 = 0b0001_0101; // 월 수 금
    let lee: u8 = 0b0001_1100; // 수 목 금
    show("kim", kim);
    show("lee", lee);
    // & 는 둘 다 켜진 자리, | 는 하나라도 켜진 자리
    show("kim & lee", kim & lee);
    show("kim | lee", kim | lee);
    // ^ 는 한쪽만 켜진 자리, ! 는 모두 뒤집기
    show("kim ^ lee", kim ^ lee);
    show("!kim", !kim);
}
