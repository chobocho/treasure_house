fn main() {
    let width = 3;
    let height = 4;
    // 중괄호 안에 변수 이름을 바로 쓴다
    println!("{width} x {height}");
    // 서식 지정은 이름 뒤에 : 을 찍고 쓴다
    let size = (width, height);
    println!("{size:?}");
    // 변수가 아닌 값에는 이름을 붙여서 넘긴다
    println!("넓이 {area}", area = width * height);
}
