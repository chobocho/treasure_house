use std::io;
use std::process::Command;

fn main() -> io::Result<()> {
    for code in ["0", "3"] {
        println!("boss: job {code} 을 돌린다");
        // status 는 자식을 돌리고, 끝날 때까지 기다린다
        let status = Command::new("./job").arg(code).status()?;
        println!(
            "boss: success {} code {:?}",
            status.success(),
            status.code()
        );
    }
    Ok(())
}
