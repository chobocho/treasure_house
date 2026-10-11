// mod shapes; — 내용은 같은 디렉터리의 shapes.rs 에 있다.
mod shapes;

fn main() {
    println!("{}", shapes::area(3, 4));
    println!("{}", shapes::circle::area(1.0));
}
