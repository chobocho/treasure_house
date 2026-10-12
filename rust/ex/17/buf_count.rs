use std::io::{self, BufWriter, Write};

// 받은 바이트는 버리고, write 가 몇 번 불렸는지만 센다
struct Counter {
    calls: usize,
    bytes: usize,
}

impl Write for Counter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.calls += 1;
        self.bytes += buf.len();
        Ok(buf.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn main() -> io::Result<()> {
    let mut direct = Counter { calls: 0, bytes: 0 };
    for n in 1..=1000 {
        writeln!(direct, "{n}번 줄")?;
    }
    println!(
        "바로      {:>4} 번, {} 바이트",
        direct.calls, direct.bytes
    );

    let mut out = BufWriter::new(Counter { calls: 0, bytes: 0 });
    for n in 1..=1000 {
        writeln!(out, "{n}번 줄")?;
    }
    // get_ref 는 감싸 둔 Counter 를 빌려 준다
    println!("flush 전  {:>4} 번", out.get_ref().calls);
    out.flush()?;
    let c = out.get_ref();
    println!("BufWriter {:>4} 번, {} 바이트", c.calls, c.bytes);
    Ok(())
}
