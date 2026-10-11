fn main() {
    // 작은따옴표 안에 글자 하나
    let latin = 'a';
    let hangul = '가';
    let crab = '🦀';
    println!("{latin} {hangul} {crab}");
    // 어느 글자든 4바이트를 차지한다
    println!("char 는 {}바이트", size_of::<char>());
    // 글자마다 유니코드 번호가 하나씩 있다
    println!("{:#x} {:#x}", latin as u32, hangul as u32);
    println!("{:#x}", crab as u32);
    // 그 번호로 글자를 적을 수도 있다
    let crab2 = '\u{1F980}';
    println!("{crab2} 같은 글자인가? {}", crab == crab2);
    // 자판으로 적기 어려운 글자는 \ 로 시작해 적는다
    let newline = '\n';
    println!("{newline:?} {:?} {:?} {:?}", '\t', '\'', '\\');
    println!("줄바꿈의 번호 {}", newline as u32);
}
