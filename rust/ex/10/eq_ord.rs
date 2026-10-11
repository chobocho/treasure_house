#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone, Copy)]
struct Version {
    major: u32,
    minor: u32,
}

fn main() {
    let a = Version {
        major: 1,
        minor: 85,
    };
    let b = Version {
        major: 1,
        minor: 99,
    };
    let c = Version { major: 2, minor: 0 };

    println!("{} {}", a == b, a != b);
    // 필드를 적은 순서대로 견준다 — major 먼저, 같으면 minor.
    println!("{} {}", a < b, b < c);
    let mut all = [c, a, b];
    all.sort();
    println!("{:?}", all.map(|v| (v.major, v.minor)));
    println!("{:?}", a.max(b));
}
