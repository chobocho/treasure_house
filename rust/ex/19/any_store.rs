use std::any::{Any, TypeId};
use std::collections::HashMap;

// 타입마다 값 하나를 맡아 두는 보관함. 어떤 타입이 올지 모른다.
#[derive(Default)]
struct Store {
    slots: HashMap<TypeId, Box<dyn Any>>,
}

impl Store {
    fn put<T: Any>(&mut self, value: T) {
        self.slots.insert(TypeId::of::<T>(), Box::new(value));
    }

    fn get<T: Any>(&self) -> Option<&T> {
        self.slots.get(&TypeId::of::<T>())?.downcast_ref::<T>()
    }
}

// 플러그인이 저마다 정한 설정 — Store 를 쓴 사람은 이 타입들을 모른다.
struct Theme(&'static str);
struct Volume(u8);

fn main() {
    let mut store = Store::default();
    store.put(Theme("dark"));
    store.put(Volume(7));
    println!("{:?}", store.get::<Theme>().map(|t| t.0));
    println!("{:?}", store.get::<Volume>().map(|v| v.0));
    println!("{}", store.get::<String>().is_none());
    // 같은 타입을 또 넣으면 그 칸이 바뀐다.
    store.put(Volume(9));
    let volume = store.get::<Volume>().map(|v| v.0);
    println!("{volume:?} {}", store.slots.len());
}
