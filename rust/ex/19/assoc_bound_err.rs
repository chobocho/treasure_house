// 무엇이든 내주는 반복자를 받아 한 줄씩 찍으려 한다.
fn print_all<I: Iterator>(items: I) {
    for x in items {
        println!("- {x}");
    }
}

fn main() {
    print_all(["a", "b"].iter());
}
//@ expect: E0277
