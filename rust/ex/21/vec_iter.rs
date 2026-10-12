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
        // 안전: T 의 크기는 0 이 아니고 new_cap 은 4 이상이라, 잡을
        // 크기가 0 이 아니다.
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

impl<T> Drop for MyVec<T> {
    fn drop(&mut self) {
        for i in 0..self.len {
            // 안전: i 번 칸에는 값이 있다(i < len). 칸마다 한 번만
            // 정리하고, 이 뒤로는 읽지 않는다.
            unsafe {
                std::ptr::drop_in_place(self.ptr.as_ptr().add(i))
            };
        }
        if self.cap != 0 {
            let layout = Self::layout(self.cap);
            // 안전: cap 이 0 이 아니니 ptr 은 이 배치로 잡은 자리다.
            // 남은 값이 없다. 한 번 돌려준다.
            unsafe { dealloc(self.ptr.as_ptr() as *mut u8, layout) };
        }
    }
}

impl<T> MyVec<T> {
    fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        // 안전: 줄이기 전의 마지막 칸에는 값이 있었다. len 을 먼저
        // 줄였으니 그 칸은 이제 값이 없는 칸이고, 다시 읽지 않는다.
        Some(unsafe { self.ptr.as_ptr().add(self.len).read() })
    }
}

// MyVec 를 통째로 넘겨받아 값을 앞에서부터 하나씩 내주는 반복자.
// next 부터 len 앞까지의 칸에만 값이 남아 있다.
struct MyIter<T> {
    ptr: NonNull<T>,
    cap: usize,
    next: usize,
    len: usize,
}

impl<T> IntoIterator for MyVec<T> {
    type Item = T;
    type IntoIter = MyIter<T>;

    fn into_iter(self) -> MyIter<T> {
        let iter = MyIter {
            ptr: self.ptr,
            cap: self.cap,
            next: 0,
            len: self.len,
        };
        // 자리와 값의 주인이 iter 로 바뀌었다. self 의 Drop 이 돌면
        // 같은 것을 두 번 정리하게 되므로, 정리하지 않고 잊는다.
        std::mem::forget(self);
        iter
    }
}

impl<T> Iterator for MyIter<T> {
    type Item = T;

    fn next(&mut self) -> Option<T> {
        if self.next == self.len {
            return None;
        }
        // 안전: next < len 이라 이 칸에는 값이 있다. 꺼낸 다음 next 를
        // 올려서 같은 칸을 다시 읽지 않는다.
        let value = unsafe { self.ptr.as_ptr().add(self.next).read() };
        self.next += 1;
        Some(value)
    }
}

impl<T> Drop for MyIter<T> {
    fn drop(&mut self) {
        for i in self.next..self.len {
            // 안전: next 부터 len 앞까지는 아직 내주지 않은 칸이라
            // 값이 있다. 칸마다 한 번만 정리한다.
            unsafe {
                std::ptr::drop_in_place(self.ptr.as_ptr().add(i))
            };
        }
        if self.cap != 0 {
            let layout = MyVec::<T>::layout(self.cap);
            // 안전: MyVec 가 이 배치로 잡은 자리를 넘겨받았고, 남은
            // 값이 없다. 한 번 돌려준다.
            unsafe { dealloc(self.ptr.as_ptr() as *mut u8, layout) };
        }
    }
}

// 정리될 때 이름을 찍는 값
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("  정리: {}", self.0);
    }
}

// 끝까지 돈다.
fn all() {
    let mut nums = MyVec::new();
    for n in 1..=6u32 {
        nums.push(n * 10);
    }
    println!("{} {}", nums.len(), nums.capacity());
    println!("{:?}", nums.pop());
    let mut total = 0;
    for n in nums {
        print!("{n} ");
        total += n;
    }
    println!("합 {total}");
}

// 다섯 가운데 둘만 받고 반복자를 버린다.
fn partly() {
    let mut v = MyVec::new();
    for name in ["a", "b", "c", "d", "e"] {
        v.push(Noisy(name));
    }
    let mut it = v.into_iter();
    for _ in 0..2 {
        if let Some(x) = it.next() {
            println!("받은 값 {}", x.0);
        }
    }
    println!("반복자를 버린다");
    drop(it);
    println!("partly 끝");
}

fn main() {
    all();
    partly();
}
