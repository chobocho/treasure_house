// 앞 예제의 두 매크로를 하나로. 속에서만 쓰는 갈래는 @go 로 시작한다.
macro_rules! opts {
    (@go $v:ident; $(,)?) => {};
    (@go $v:ident; $key:ident = $val:expr, $($rest:tt)*) => {
        $v.push((stringify!($key), $val.to_string()));
        opts!(@go $v; $($rest)*);
    };
    (@go $v:ident; $key:ident, $($rest:tt)*) => {
        $v.push((stringify!($key), true.to_string()));
        opts!(@go $v; $($rest)*);
    };
    // 부르는 쪽이 쓰는 갈래. 무엇이든 받으므로 맨 아래에 둔다.
    ($($all:tt)*) => {{
        let mut v = Vec::new();
        opts!(@go v; $($all)* ,);
        v
    }};
}

fn main() {
    let a = opts!(verbose, level = 3, name = "rs", dry_run);
    println!("{a:?}");
    let b = opts!(quiet, jobs = 2 + 2,);
    println!("{b:?}");
}
