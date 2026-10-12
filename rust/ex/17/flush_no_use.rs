use std::io;

fn main() -> io::Result<()> {
    print!("내려받는 중 ... ");
    io::stdout().flush()?;
    println!("끝");
    Ok(())
}
//@ expect: E0599
