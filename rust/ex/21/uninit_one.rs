use std::mem::MaybeUninit;

fn main() {
    // 값이 아직 없는 u32 한 칸. 만드는 것은 안전하다.
    let mut slot = MaybeUninit::<u32>::uninit();
    println!("{}", size_of::<MaybeUninit<u32>>());

    // write 도 안전하다. 넣은 값을 가리키는 가변 참조를 돌려준다.
    let r: &mut u32 = slot.write(7);
    *r += 1;

    // 안전: 바로 위에서 write 로 값을 넣었다.
    let n: u32 = unsafe { slot.assume_init() };
    println!("{n}");
}
