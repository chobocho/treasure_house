// 상수는 타입을 꼭 적는다. 이름은 대문자와 밑줄로 쓴다
const MAX_PLAYERS: u32 = 8;
// 값은 컴파일할 때 계산된다
const SECONDS_PER_DAY: u32 = 60 * 60 * 24;

fn main() {
    println!("최대 {MAX_PLAYERS}명");
    println!("하루는 {SECONDS_PER_DAY}초");
    // 함수 안에도 둘 수 있다
    const HALF: u32 = MAX_PLAYERS / 2;
    println!("절반은 {HALF}명");
}
