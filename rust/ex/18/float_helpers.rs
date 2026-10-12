fn main() {
    // 두 점 사이의 거리 — 가로 3, 세로 4
    let (dx, dy): (f64, f64) = (3.0, 4.0);
    println!("sqrt       {}", (dx * dx + dy * dy).sqrt());
    println!("hypot      {}", dx.hypot(dy));
    // 같은 삼각형을 2 의 600 제곱 배로 키운다
    let k = 2_f64.powi(600);
    let (bx, by) = (dx * k, dy * k);
    // 제곱이 f64 의 끝을 넘어 무한대가 된다
    println!("bx * bx    {}", bx * bx);
    println!("큰 sqrt    {}", (bx * bx + by * by).sqrt() / k);
    println!("큰 hypot   {}", bx.hypot(by) / k);

    // 각도를 0 이상 360 미만으로
    let angle: f64 = -90.0;
    println!("%          {}", angle % 360.0);
    println!("rem_euclid {}", angle.rem_euclid(360.0));
    // 값을 0 과 1 사이에 가둔다
    for x in [-0.2_f64, 0.4, 1.7] {
        println!("clamp      {x} → {}", x.clamp(0.0, 1.0));
    }
    // 부호만 남긴다
    println!("signum     {} {}", 2.5_f64.signum(), (-2.5_f64).signum());
}
