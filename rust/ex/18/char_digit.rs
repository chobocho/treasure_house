fn main() {
    // to_digit — 숫자 글자를 수로. 숫자만 골라 자릿수를 더한다
    let card = "4012-8888";
    let sum: u32 = card.chars().filter_map(|c| c.to_digit(10)).sum();
    println!("{sum}");

    // from_digit — 수를 숫자 글자로. 둘째 인자가 진법이다
    println!("{:?}", char::from_digit(7, 10));
    println!("{:?}", char::from_digit(11, 16));
    println!("{:?}", char::from_digit(11, 10));

    // 13 을 2 진수 글로 — 낮은 자리부터 뽑아서 뒤집는다
    let mut n = 13_u32;
    let mut low_first = String::new();
    while n > 0 {
        low_first.push(char::from_digit(n % 2, 2).unwrap());
        n /= 2;
    }
    let bits: String = low_first.chars().rev().collect();
    println!("{low_first} {bits} {:b}", 13);

    // repeat — 같은 글을 n 번 잇는다
    let title = "report";
    println!("{title}\n{}", "=".repeat(title.len()));
    println!("{}", "ab".repeat(3));

    // make_ascii_uppercase — 그 String 을 제자리에서 고친다
    let mut code = String::from("ab-12-가나");
    code.make_ascii_uppercase();
    println!("{code}");
}
