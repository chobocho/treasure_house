struct MyBox<T>(T);

fn main() {
    let b = MyBox(5);
    println!("{}", *b + 1);
}
//@ expect: E0614
