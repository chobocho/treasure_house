fn main() {
    let x = 2.5_f64;
    let y = -2.5_f64;
    println!("        {x:>4} {y:>4}");
    println!("round   {:>4} {:>4}", x.round(), y.round());
    println!("floor   {:>4} {:>4}", x.floor(), y.floor());
    println!("ceil    {:>4} {:>4}", x.ceil(), y.ceil());
    println!("trunc   {:>4} {:>4}", x.trunc(), y.trunc());
    // {:?} 로 찍으면 결과가 여전히 실수임이 보인다
    println!("{:?} {:?}", x.round(), y.trunc());
    // 제곱근과 거듭제곱
    println!("2 의 제곱근   {}", 2.0_f64.sqrt());
    println!("1.5 의 세제곱 {}", 1.5_f64.powi(3));
    println!("-1 의 제곱근  {}", (-1.0_f64).sqrt());
    // 찍을 때만 반올림하려면 서식의 정밀도를 쓴다
    println!("{:.1} {:.0}", 2.0_f64.sqrt(), 2.0_f64.sqrt());
}
