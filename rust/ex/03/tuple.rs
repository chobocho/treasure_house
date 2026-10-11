use std::any::type_name_of_val;

fn main() {
    // 타입이 서로 다른 값 셋을 하나로 묶는다
    let student = ("민지", 17, 91.5);
    println!("{student:?}");
    println!("{}", type_name_of_val(&student));
    // 점 뒤에 번호를 적어 꺼낸다 — 0 부터 센다
    println!("{} {}", student.0, student.2);
    // 한 번에 풀어 칸마다 이름을 붙인다
    let (name, age, score) = student;
    println!("{name}: {age}살, {score}점");
    // 두 값을 맞바꾼다
    let (a, b) = (1, 2);
    let (a, b) = (b, a);
    println!("a = {a}, b = {b}");
    // 아무것도 묶지 않은 튜플 () 도 값이다
    let nothing = ();
    println!("값 {nothing:?}, 타입 {}", type_name_of_val(&nothing));
}
