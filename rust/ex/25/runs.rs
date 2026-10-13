use std::io;

// 이어진 같은 줄을 한 덩어리로 세어 찍는다.
fn main() -> io::Result<()> {
    let mut prev = String::new();
    let mut count = 0;
    let mut groups = 0;
    for line in io::stdin().lines() {
        let line = line?;
        if count > 0 && line == prev {
            count += 1;
        } else {
            if count > 0 {
                println!("{count:>3} [{prev}]");
            }
            prev = line;
            count = 1;
            groups += 1;
        }
    }
    // 마지막 덩어리는 반복문이 끝난 뒤에 찍는다.
    if count > 0 {
        println!("{count:>3} [{prev}]");
    }
    println!("{groups}덩어리");
    Ok(())
}
//@ stdin: \n\n맑음\n맑음\n맑음\n비\n맑음\n눈\n눈
