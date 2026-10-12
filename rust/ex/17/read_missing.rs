use std::fs;
use std::io::ErrorKind;

fn main() {
    match fs::read_to_string("none.txt") {
        Ok(text) => println!("{text}"),
        // e 의 타입은 std::io::Error 다
        Err(e) => {
            println!("{e}");
            println!("{e:?}");
            println!("{:?}", e.kind());
            println!("{}", e.kind() == ErrorKind::NotFound);
        }
    }
}
