use std::io::{self, Write};

fn main() -> io::Result<()> {
    print!("내려받는 중 ... ");
    // 모아 둔 글을 지금 내보낸다
    io::stdout().flush()?;
    eprint!("(알림: 3초쯤 걸린다) ");
    println!("끝");
    Ok(())
}
