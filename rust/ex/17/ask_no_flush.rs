use std::io;

// ask.rs 에서 flush 만 뺐다 — 묻는 말이 버퍼에 남은 채로 읽는다
fn ask(question: &str) -> io::Result<String> {
    print!("{question} ");
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
