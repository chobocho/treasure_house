// 2024 에디션: static mut 의 참조를 만들면 바로 오류(static_mut_refs).
static mut SCORE: u32 = 0;

fn main() {
    unsafe {
        SCORE += 100;
        let s = &SCORE;
        println!("{s}");
    }
}
