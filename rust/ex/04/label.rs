fn main() {
    // 안쪽 반복문에서 바깥 반복문을 끝내려면 이름표를 붙인다.
    'outer: for a in 1..10 {
        for b in 1..10 {
            if a * b == 42 {
                println!("{a} x {b} = 42");
                break 'outer;
            }
        }
    }
}
