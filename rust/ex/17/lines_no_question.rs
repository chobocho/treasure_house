use std::io;

fn main() -> io::Result<()> {
    for line in io::stdin().lines() {
        println!("{}", line.trim());
    }
    Ok(())
}
//@ expect: E0599
