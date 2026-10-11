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
    println!("{}", a == b);
}
//@ expect: E0369
