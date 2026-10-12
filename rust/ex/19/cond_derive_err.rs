#[derive(Debug)]
struct Labeled<T> {
    label: &'static str,
    value: T,
}

struct Raw;

fn main() {
    let port = Labeled {
        label: "port",
        value: 8080,
    };
    println!("{} {}", port.label, port.value);
    println!("{port:?}");
    let raw = Labeled {
        label: "raw",
        value: Raw,
    };
    println!("{raw:?}");
    println!("{:?}", vec![Raw]);
}
//@ expect: E0277
