use std::marker::PhantomPinned;
use std::mem;
use std::pin::Pin;
use std::ptr;

// at 은 같은 값의 text 를 가리키게 할 포인터다.
struct Tagged {
    text: String,
    at: *const String,
    // 이 필드가 있으면 Tagged 는 Unpin 이 아니다.
    _pin: PhantomPinned,
}

impl Tagged {
    // at 이 지금의 text 를 가리키는가. 주소만 견주고 따라가지 않는다.
    fn points_to_self(&self) -> bool {
        ptr::eq(self.at, &self.text)
    }
}

// 상자에 담아 at 을 적은 뒤에, 그 상자를 Pin 으로 감싸서 내준다.
fn pinned(text: &str) -> Pin<Box<Tagged>> {
    let mut tag = Box::new(Tagged {
        text: String::from(text),
        at: ptr::null(),
        _pin: PhantomPinned,
    });
    tag.at = &raw const tag.text;
    Box::into_pin(tag)
}

fn main() {
    let mut a = pinned("ferris");
    let mut b = pinned("corro");
    println!("감싼 뒤: {} {}", a.points_to_self(), b.points_to_self());

    // 상자끼리 맞바꾼다. 값은 힙의 제자리에 있다.
    mem::swap(&mut a, &mut b);
    println!("{}: {}", a.text, a.points_to_self());
    println!("{}: {}", b.text, b.points_to_self());

    // 이번에는 상자 속의 값끼리 맞바꾼다.
    mem::swap(&mut *a, &mut *b);
    println!("{}: {}", a.text, a.points_to_self());
    println!("{}: {}", b.text, b.points_to_self());
}
//@ expect: E0596
