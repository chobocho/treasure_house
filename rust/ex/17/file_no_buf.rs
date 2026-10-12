use std::fs::File;
use std::io::{self, BufRead};

fn main() -> io::Result<()> {
    let file = File::open("scores.txt")?;
    for line in file.lines() {
        println!("{}", line?);
    }
    Ok(())
}
//@ expect: E0599
