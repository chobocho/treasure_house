use std::io::{self, Write};

// 묻는 말을 찍고, 한 줄을 읽어 돌려준다
fn ask(question: &str) -> io::Result<String> {
    print!("{question} ");
    // 줄바꿈이 없는 글이라 직접 내보낸다
    io::stdout().flush()?;
    let mut line = String::new();
    io::stdin().read_line(&mut line)?;
    Ok(line.trim().to_string())
}

fn main() -> io::Result<()> {
    let name = ask("이름:")?;
    eprintln!("<- {name:?} 를 읽었다");
    println!("안녕하세요, {name} 님");
    Ok(())
}
//@ stdin: Ferris\n
