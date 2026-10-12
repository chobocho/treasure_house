// 슬라이스 둘을 칸끼리 더한다. 길이는 실행 중에야 안다.
fn add(a: &[i32], b: &[i32]) -> Result<Vec<i32>, String> {
    if a.len() != b.len() {
        return Err(format!(
            "길이가 다르다: {} 과 {}",
            a.len(),
            b.len()
        ));
    }
    Ok(a.iter().zip(b).map(|(x, y)| x + y).collect())
}

fn main() {
    println!("{:?}", add(&[1, 2, 3], &[10, 20, 30]));
    println!("{:?}", add(&[1, 2, 3], &[10, 20]));
}
