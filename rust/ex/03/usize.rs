use std::any::type_name_of_val;

fn main() {
    let word = "rust";
    let scores = [70, 85, 90];
    // 길이는 늘 usize 로 돌아온다
    let n = word.len();
    println!("글자 {n}개 ({})", type_name_of_val(&n));
    println!("점수 {}개", scores.len());
    // 몇 번째인지를 가리키는 수도 usize 다
    let last: usize = scores.len() - 1;
    println!("마지막 점수: {}", scores[last]);
    println!("usize 는 {}비트", usize::BITS);
}
