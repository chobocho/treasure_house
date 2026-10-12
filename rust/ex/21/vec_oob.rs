use std::alloc::{Layout, alloc, dealloc, handle_alloc_error};
use std::ptr::NonNull;

// 손으로 만드는 벡터. 세 필드가 늘 지키는 약속:
//   cap == 0 이면 잡은 자리가 없고, ptr 은 따라가지 않는다.
//   cap != 0 이면 ptr 은 layout(cap) 으로 잡은 자리의 맨 앞이다.
//   len <= cap 이고, 앞에서부터 len 칸에만 값이 있다.
struct MyVec<T> {
    ptr: NonNull<T>,
    cap: usize,
    len: usize,
}

impl<T> MyVec<T> {
    fn new() -> Self {
        // 크기가 0 인 타입은 받지 않는다. 컴파일할 때 걸러 낸다.
        const { assert!(size_of::<T>() != 0, "MyVec: 크기 0 인 타입") };
        MyVec {
            ptr: NonNull::dangling(),
            cap: 0,
            len: 0,
        }
    }

    fn len(&self) -> usize {
        self.len
    }

    fn capacity(&self) -> usize {
        self.cap
    }

    // T 가 cap 칸인 자리의 배치. 받아 줄 수 없게 크면 패닉한다.
    fn layout(cap: usize) -> Layout {
        match Layout::array::<T>(cap) {
            Ok(layout) => layout,
            Err(_) => panic!("MyVec: 자리가 너무 크다"),
        }
    }

    // 더 큰 자리를 잡아 값을 옮기고, 옛 자리를 돌려준다.
    fn grow(&mut self) {
        let new_cap = match self.cap {
            0 => 4,
            n => n.saturating_mul(2),
        };
        let new_layout = Self::layout(new_cap);
        // 안전: new 가 크기 0 인 T 를 걸러 냈고 new_cap 은 4 이상이라,
        // 잡을 크기가 0 이 아니다.
        let raw = unsafe { alloc(new_layout) };
        let Some(new_ptr) = NonNull::new(raw as *mut T) else {
            handle_alloc_error(new_layout)
        };
        for i in 0..self.len {
            // 안전: 옛 자리의 i 번 칸에는 값이 있다(i < len). 새 자리는
            // len 칸보다 크다. 꺼낸 칸은 다시 읽지도 정리하지도 않는다.
            unsafe {
                let value = self.ptr.as_ptr().add(i).read();
                new_ptr.as_ptr().add(i).write(value);
            }
        }
        if self.cap != 0 {
            let old = Self::layout(self.cap);
            // 안전: 옛 자리는 이 배치로 잡았고, 값은 모두 옮겼다. 값을
            // 정리하지 않고 자리만 한 번 돌려준다.
            unsafe { dealloc(self.ptr.as_ptr() as *mut u8, old) };
        }
        self.ptr = new_ptr;
        self.cap = new_cap;
    }

    fn push(&mut self, value: T) {
        if self.len == self.cap {
            self.grow();
        }
        // 안전: len < cap 이라 len 번 칸은 잡은 자리 안이고, 아직 값이
        // 없다. 그래서 대입이 아니라 write 로 넣는다.
        unsafe { self.ptr.as_ptr().add(self.len).write(value) };
        self.len += 1;
    }
}

// 값이 든 앞 len 칸을 슬라이스로 빌려준다.
impl<T> std::ops::Deref for MyVec<T> {
    type Target = [T];

    fn deref(&self) -> &[T] {
        // 안전: ptr 은 널이 아니고 정렬이 맞다. 자리가 없을 때의
        // dangling 도 그렇고, 그때는 len 이 0 이다. 앞 len 칸은 한
        // 자리 안이고 값이 있다. 슬라이스는 &self 를 빌린 동안만 산다.
        unsafe {
            std::slice::from_raw_parts(self.ptr.as_ptr(), self.len)
        }
    }
}

fn main() {
    let mut v = MyVec::new();
    let mut std_v = Vec::new();
    for n in 1..=5u32 {
        v.push(n * 10);
        std_v.push(n * 10);
    }
    println!("{} {}", v.len(), v.capacity());
    println!("{} {}", v[0], v[5]);
    println!("{:?}", &v[1..3]);
    println!("{}", v.iter().sum::<u32>());
    println!("{:?} {}", v.first(), v.contains(&30));
    println!("{}", v[..] == std_v[..]);
}
//@ exit: 101
