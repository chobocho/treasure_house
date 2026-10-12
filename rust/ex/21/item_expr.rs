// 정의를 통째로 받아, derive(Debug) 를 붙여 다시 내놓는다.
macro_rules! debuggable {
    ($($def:expr)*) => {
        $(
            #[derive(Debug)]
            $def
        )*
    };
}

debuggable! {
    struct Point {
        x: i32,
        y: i32,
    }

    enum Light {
        Red,
        Green,
    }
}

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{p:?} {}", p.x + p.y);
    println!("{:?} {:?}", Light::Red, Light::Green);
}
//@ expect: error
