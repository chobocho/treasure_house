fn main() {
    let point = (3, 4);
    let primes = [2, 3, 5, 7];
    // {:?} 는 개발자가 들여다보라고 찍는 디버그 출력이다
    println!("점: {:?}", point);
    println!("소수: {:?}", primes);
    // 문자열은 따옴표와 이스케이프까지 보인다
    println!("{}", "탭\t하나");
    println!("{:?}", "탭\t하나");
}
