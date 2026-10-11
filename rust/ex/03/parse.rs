fn main() {
    let text = "42";
    // ① 받는 변수의 타입 표기로 알려 준다
    let a: i32 = text.parse().expect("수가 아니다");
    // ② 터보피시 ::<타입> 으로 parse 에 직접 알려 준다
    let b = text.parse::<u8>().expect("수가 아니다");
    let c = "3.5".parse::<f64>().expect("수가 아니다");
    let d = "true".parse::<bool>().expect("불이 아니다");
    println!("{a} {b} {c} {d}");
    // 실패하면 Err 다 — 까닭이 안에 들어 있다
    println!("{:?}", "4x".parse::<i32>());
    println!("{:?}", "300".parse::<u8>());
    println!("{:?}", " 42".parse::<i32>());
    println!("{:?}", "".parse::<i32>());
}
