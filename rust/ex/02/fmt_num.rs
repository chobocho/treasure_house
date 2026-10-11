fn main() {
    let price = 1234.5678;
    // .N — 소수점 아래 N 자리로 반올림한다
    println!("{:.2}", price);
    println!("{:.0}", price);
    // 폭과 함께 — 전체 10칸, 소수 1자리
    println!("[{:10.1}]", price);
    // + 는 양수에도 부호를 붙인다
    println!("{:+} {:+}", 7, -7);
    // 폭 앞의 0 — 빈자리를 0 으로, 부호는 맨 앞에
    println!("{:05} {:05}", 42, -42);
    println!("{:+010.2}", price);
    // 문자열의 .N 은 앞에서 N 글자만 남긴다
    println!("{:.3}", "abcdef");
}
