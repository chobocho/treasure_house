use std::io;

fn main() -> io::Result<()> {
    // lines() 는 줄을 하나씩 내는 반복자다
    for line in io::stdin().lines() {
        // 원소는 io::Result<String> — 읽기는 실패할 수 있다
        let line = line?;
        println!("{line:?}");
    }
    println!("입력 끝");
    Ok(())
}
//@ stdin: kim\n\nlee
