fn main() {
    let a = 17;
    let b = 5;
    // 산술 — 두 값으로 새 값을 만든다
    println!("{} {} {}", a + b, a - b, a * b);
    println!("{} {}", a / b, a % b);
    // - 를 값 하나 앞에 붙이면 부호가 뒤집힌다
    println!("{}", -a);
    // 비교 — 답은 true 아니면 false 다
    println!("{} {}", a == b, a != b);
    println!("{} {} {} {}", a < b, a <= b, a > b, a >= b);
    // 복합 대입 — 셈한 결과를 왼쪽 변수에 다시 넣는다
    let mut n = 10;
    n += 5;
    println!("{n}");
    n -= 3;
    println!("{n}");
    n *= 2;
    println!("{n}");
    n /= 5;
    println!("{n}");
    n %= 3;
    println!("{n}");
}
