#[derive(Ord, PartialOrd, Eq)]
struct Version {
    major: u32,
    minor: u32,
}

fn main() {
    let v = Version {
        major: 1,
        minor: 85,
    };
    println!("{}.{}", v.major, v.minor);
}
//@ expect: E0277
