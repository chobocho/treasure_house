// 2024 에디션: no_mangle 은 이름 충돌을 일으킬 수 있어 unsafe 속성이 됐다.
#[no_mangle]
pub extern "C" fn tt_tick(dt: u32) -> u32 {
    dt
}

fn main() {
    println!("{}", tt_tick(16));
}
