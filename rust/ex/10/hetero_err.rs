struct Circle(f64);
struct Square(f64);

fn main() {
    let shapes = vec![Circle(1.0), Square(2.0)];
    println!("{}", shapes.len());
}
//@ expect: E0308
