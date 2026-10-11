fn main() {
    let composed = "é"; // 한 글자짜리 é (U+00E9)
    let combined = "e\u{301}"; // e 뒤에 악센트 부호를 붙인 것

    // 화면에서는 같아 보이지만 char 의 수가 다르다.
    println!("{composed} {combined}");
    println!(
        "{} {}",
        composed.chars().count(),
        combined.chars().count()
    );
    println!("{}", composed == combined);
    let flag = "🇰🇷";
    println!(
        "{flag} {} 글자, {} 바이트",
        flag.chars().count(),
        flag.len()
    );
}
