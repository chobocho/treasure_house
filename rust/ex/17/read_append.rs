use std::io;

fn main() -> io::Result<()> {
    let mut line = String::new();
    // 비우지 않고 같은 String 에 두 번 읽는다
    io::stdin().read_line(&mut line)?;
    println!("{line:?}");
    io::stdin().read_line(&mut line)?;
    println!("{line:?}");
    Ok(())
}
//@ stdin: kim\nlee\n
