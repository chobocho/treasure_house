use std::fmt;
use std::ops::Add;
use std::str::FromStr;

#[derive(Clone, Copy)]
struct Frac {
    n: u64,
    d: u64,
}

fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl Frac {
    // 만들 때 약분해 둔다. d 는 0 이 아니어야 한다.
    fn new(n: u64, d: u64) -> Frac {
        let g = gcd(n, d);
        Frac { n: n / g, d: d / g }
    }
}

impl fmt::Display for Frac {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if self.d == 1 {
            write!(f, "{}", self.n)
        } else {
            write!(f, "{}/{}", self.n, self.d)
        }
    }
}

impl Add for Frac {
    type Output = Frac;

    fn add(self, other: Frac) -> Frac {
        Frac::new(self.n * other.d + other.n * self.d, self.d * other.d)
    }
}

impl FromStr for Frac {
    type Err = String;

    fn from_str(s: &str) -> Result<Frac, String> {
        // '/' 가 없으면 분모가 1 인 분수다.
        let (n, d) = s.split_once('/').unwrap_or((s, "1"));
        let n: u64 =
            n.parse().map_err(|_| format!("수가 아니다: {n}"))?;
        let d: u64 =
            d.parse().map_err(|_| format!("수가 아니다: {d}"))?;
        if d == 0 {
            return Err(String::from("분모가 0 이다"));
        }
        Ok(Frac::new(n, d))
    }
}

fn add_text(a: &str, b: &str) -> Result<Frac, String> {
    let a: Frac = a.parse()?;
    let b: Frac = b.parse()?;
    Ok(a + b)
}

fn main() {
    let pairs = [
        ("1/2", "1/3"),
        ("1/6", "1/3"),
        ("3/4", "5/4"),
        ("2", "6/8"),
        ("0/5", "0"),
        ("1/2", "x/3"),
        ("5/y", "1"),
        ("1/0", "1/2"),
    ];
    for (a, b) in pairs {
        match add_text(a, b) {
            Ok(sum) => println!("{a} + {b} = {sum}"),
            Err(why) => println!("{a} + {b} -> 오류: {why}"),
        }
    }
    let half = Frac::new(2, 4);
    println!("{half} + {half} + {half} = {}", half + half + half);
}
