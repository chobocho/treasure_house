use std::fs;
use std::io;

fn main() -> io::Result<()> {
    fs::write("a.txt", "hello\n")?;

    // copy 는 옮긴 바이트 수를 돌려준다
    let n = fs::copy("a.txt", "b.txt")?;
    println!("copy: {n} 바이트");
    println!("b.txt {:?}", fs::read_to_string("b.txt"));

    // rename 뒤에는 옛 이름으로 읽지 못한다
    fs::rename("b.txt", "c.txt")?;
    let old = fs::read_to_string("b.txt");
    println!("b.txt {:?}", old.map_err(|e| e.kind()));
    println!("c.txt {:?}", fs::read_to_string("c.txt"));

    fs::remove_file("c.txt")?;
    // 이미 지운 파일을 또 지우면 오류다
    let again = fs::remove_file("c.txt");
    println!("remove {:?}", again.map_err(|e| e.kind()));
    println!("a.txt {:?}", fs::read_to_string("a.txt"));
    Ok(())
}
