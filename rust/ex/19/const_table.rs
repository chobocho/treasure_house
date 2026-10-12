// for 대신 while 로 돈다.
const fn squares<const N: usize>() -> [u32; N] {
    let mut out = [0; N];
    let mut i = 0;
    while i < N {
        out[i] = (i * i) as u32;
        i += 1;
    }
    out
}

// 십진수로 몇 자리인가
const fn digits(mut n: u32) -> usize {
    let mut count = 1;
    while n >= 10 {
        n /= 10;
        count += 1;
    }
    count
}

const TABLE: [u32; 6] = squares();
// 표의 마지막 값 25 의 자릿수
const WIDTH: usize = digits(TABLE[5]);

fn main() {
    println!("{TABLE:?}");
    // WIDTH 가 배열의 길이로 쓰인다.
    let rule = [b'-'; WIDTH];
    println!("{}", rule.len());
    // 같은 함수를 실행 중에 읽은 수로 부른다.
    let n: u32 = "12345".parse().unwrap();
    println!("{n} {}", digits(n));
}
