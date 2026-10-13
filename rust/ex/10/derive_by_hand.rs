#[derive(PartialEq)]
struct Derived {
    major: u32,
    minor: u32,
}

struct ByHand {
    major: u32,
    minor: u32,
}

// derive 에 부탁하지 않고 손으로 쓴 PartialEq
impl PartialEq for ByHand {
    fn eq(&self, other: &Self) -> bool {
        self.major == other.major && self.minor == other.minor
    }
}

fn main() {
    let a = Derived { major: 1, minor: 2 };
    let b = Derived { major: 1, minor: 2 };
    let c = Derived { major: 1, minor: 3 };
    println!("{} {} {}", a == b, a == c, a != c);

    let a = ByHand { major: 1, minor: 2 };
    let b = ByHand { major: 1, minor: 2 };
    let c = ByHand { major: 1, minor: 3 };
    println!("{} {} {}", a == b, a == c, a != c);
}
