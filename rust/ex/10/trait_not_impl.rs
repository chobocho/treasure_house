trait Shape {
    fn area(&self) -> f64;
}

fn print_area(shape: &impl Shape) {
    println!("{:.2}", shape.area());
}

fn main() {
    print_area(&5.0);
}
//@ expect: E0277
