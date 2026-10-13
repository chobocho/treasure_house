fn total(words: &[&str]) -> u32 {
    let mut sum = 0;
    for w in words {
        // continue 의 타입은 ! — u32 가 올 갈래에 놓인다
        let n: u32 = match w.parse() {
            Ok(n) => n,
            Err(_) => continue,
        };
        // break 와 return 도 값이 올 자리에 놓인다
        let n = if n == 0 { break } else { n };
        let n = if n > 100 { return 0 } else { n };
        sum += n;
    }
    sum
}

// break 없는 loop — 뒤에 돌려줄 식을 쓰지 않았다
fn first_even(start: u32) -> u32 {
    let mut n = start;
    loop {
        if n % 2 == 0 {
            return n;
        }
        n += 1;
    }
}

fn main() {
    println!("{}", total(&["3", "x", "4"]));
    println!("{}", total(&["3", "0", "4"]));
    println!("{}", total(&["3", "500", "4"]));
    println!("{}", first_even(7));
}
