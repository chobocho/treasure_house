struct Lock(&'static str);

impl Drop for Lock {
    fn drop(&mut self) {
        println!("{} 풀림", self.0);
    }
}

fn main() {
    let lock = Lock("잠금");
    lock.drop();
}
//@ expect: E0040
