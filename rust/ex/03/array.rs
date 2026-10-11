use std::any::type_name_of_val;

fn main() {
    // 같은 타입의 값을 정해진 개수만큼 늘어놓는다
    let scores = [70, 85, 90];
    // [값; 개수] — 같은 값으로 채운다
    let zeros = [0_u8; 5];
    println!("{scores:?} ({})", type_name_of_val(&scores));
    println!("{zeros:?} ({})", type_name_of_val(&zeros));
    println!("길이 {} 과 {}", scores.len(), zeros.len());
    // 대괄호 안에 번호를 적어 꺼낸다 — 0 부터 센다
    let last = scores.len() - 1;
    println!("첫째 {}, 마지막 {}", scores[0], scores[last]);
    // mut 배열은 칸의 값을 바꿀 수 있다
    let mut days = [31; 12];
    days[1] = 28;
    println!("{days:?}");
}
