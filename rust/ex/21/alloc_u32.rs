use std::alloc::{Layout, alloc, dealloc, handle_alloc_error};

fn main() {
    // u32 세 칸의 크기와 정렬을 묶은 값
    let layout = Layout::array::<u32>(3).unwrap();
    println!("{}", layout.size());
    println!("{}", layout.align() == align_of::<u32>());

    // 안전: layout 의 크기는 12 로, 0 이 아니다.
    let raw: *mut u8 = unsafe { alloc(layout) };
    if raw.is_null() {
        // 자리를 얻지 못했다. 표준 라이브러리가 정한 방식으로 멈춘다.
        handle_alloc_error(layout);
    }
    let p = raw as *mut u32;

    // 안전: p 는 u32 세 칸짜리 자리의 맨 앞이고 u32 에 맞게 정렬돼
    // 있다. 0·1·2 번 칸만 쓰고, 세 칸을 모두 채운 뒤에만 읽는다.
    unsafe {
        for i in 0..3 {
            p.add(i).write(10 * (i as u32 + 1));
        }
        println!("{} {} {}", *p, *p.add(1), *p.add(2));
    }

    // 안전: raw 는 위의 alloc 이 이 layout 으로 준 자리이고, 아직
    // 돌려주지 않았다. 이 뒤로는 raw 도 p 도 쓰지 않는다.
    unsafe { dealloc(raw, layout) };
}
