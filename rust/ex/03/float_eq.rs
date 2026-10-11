fn main() {
    let sum: f64 = 0.1 + 0.2;
    println!("0.1 + 0.2 = {sum}");
    println!("sum == 0.3 ? {}", sum == 0.3);
    // 두 값의 차이가 충분히 작으면 같다고 본다
    let diff = (sum - 0.3).abs();
    println!("차이 = {diff:e}");
    println!("차이 < 1e-9 ? {}", diff < 1e-9);
    // 2 의 거듭제곱으로 떨어지는 수는 어긋나지 않는다
    println!("0.5 + 0.25 == 0.75 ? {}", 0.5 + 0.25 == 0.75);
}
