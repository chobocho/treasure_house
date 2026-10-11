fn main() {
    for n in 1..=10 {
        if n % 3 != 0 {
            continue; // 아래를 건너뛰고 다음 바퀴로
        }
        print!("{n} ");
    }
    println!();
}
