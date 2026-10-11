fn main() {
    let mut found = 0;
    for a in 1..10 {
        for b in 1..10 {
            if a * b == 42 {
                found += 1;
                break; // 안쪽 for 만 끝난다
            }
        }
    }
    println!("{found}번 찾았다");
}
