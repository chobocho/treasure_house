// "B7" 같은 자리 이름을 (줄 번호, 칸 번호) 로 바꾼다.
// 번호는 둘 다 0 부터 센다. 맞지 않는 이름이면 None 이다.
fn seat(label: &str) -> Option<(usize, usize)> {
    match label.as_bytes() {
        [row @ b'A'..=b'E', col @ b'1'..=b'9'] => {
            Some(((*row - b'A') as usize, (*col - b'1') as usize))
        }
        _ => None,
    }
}

fn main() {
    let mut taken = [[false; 9]; 5];
    for label in ["B7", "E1", "F3", "A0", "C12", "A", "b7", "B7"] {
        let Some((row, col)) = seat(label) else {
            println!("{label}: 없는 자리");
            continue;
        };
        if taken[row][col] {
            println!("{label}: 이미 찬 자리");
        } else {
            taken[row][col] = true;
            println!("{label}: 예약 ({row}, {col})");
        }
    }
}
