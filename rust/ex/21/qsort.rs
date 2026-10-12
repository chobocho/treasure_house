use std::cmp::Ordering;
use std::ffi::{c_int, c_void};

// C 가 부를 함수의 타입. 두 칸의 포인터를 받아 int 를 돌려준다.
type Cmp = unsafe extern "C" fn(*const c_void, *const c_void) -> c_int;

unsafe extern "C" {
    // size 바이트짜리 n 칸을 cmp 의 답대로 줄 세운다.
    unsafe fn qsort(base: *mut c_void, n: usize, size: usize, cmp: Cmp);
}

// 두 칸을 견줘 음수, 0, 양수 가운데 하나를 준다.
unsafe extern "C" fn by_value(
    a: *const c_void,
    b: *const c_void,
) -> c_int {
    // 안전: qsort 는 넘겨받은 배열의 칸을 가리키는 포인터만 넘긴다.
    // 이 함수는 i32 의 배열에만 쓴다.
    let (a, b) = unsafe { (*(a as *const i32), *(b as *const i32)) };
    a.cmp(&b) as c_int
}

fn main() {
    let less = Ordering::Less as c_int;
    let equal = Ordering::Equal as c_int;
    let greater = Ordering::Greater as c_int;
    println!("{less} {equal} {greater}");

    let mut xs = [i32::MAX, -5, 3, i32::MIN, 0, 3];
    let mut expected = xs.to_vec();
    expected.sort();
    // 안전: xs 는 살아 있는 i32 여섯 칸이고, 칸 수와 칸의 크기를 맞게
    // 넘긴다. by_value 는 패닉하지 않고, 받은 포인터를 남겨 두지
    // 않는다.
    unsafe {
        let base = xs.as_mut_ptr() as *mut c_void;
        qsort(base, xs.len(), size_of::<i32>(), by_value);
    }
    println!("{xs:?}");
    println!("{}", xs[..] == expected[..]);
}
