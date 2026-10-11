use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    let n: i32 = "12".parse()?;
    let x: f64 = "1.5".parse()?;
    println!("{}", n as f64 * x);
    let bad: u8 = "300".parse()?;
    println!("{bad}");
    Ok(())
}
//@ exit: 1
