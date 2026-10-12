use std::io::{self, BufWriter, Write};

// 쓰기가 늘 실패하는 곳 — 가득 찬 디스크 흉내
struct Full {
    tries: u32,
}

impl Write for Full {
    fn write(&mut self, _buf: &[u8]) -> io::Result<usize> {
        self.tries += 1;
        Err(io::Error::other("가득 찼다"))
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn main() {
    let mut disk = Full { tries: 0 };
    {
        let mut out = BufWriter::new(&mut disk);
        // 버퍼에 담기만 하므로 성공이다
        println!("writeln: {:?}", writeln!(out, "중요한 글"));
    } // flush 를 부르지 않고 정리된다
    println!("정리 뒤: 쓰기 시도 {} 번", disk.tries);

    let mut out = BufWriter::new(&mut disk);
    println!("writeln: {:?}", writeln!(out, "중요한 글"));
    // 직접 부르면 실패가 Result 로 돌아온다
    println!("flush:   {:?}", out.flush());
}
