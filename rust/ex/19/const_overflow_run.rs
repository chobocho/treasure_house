const fn kib(n: u32) -> u32 {
    n * 1024
}

fn main() {
    // 같은 수를 실행 중에 읽어서 넘긴다.
    let n: u32 = "4194304".parse().unwrap();
    println!("{}", kib(4));
    println!("{}", kib(n));
}
//@ exit: 101
