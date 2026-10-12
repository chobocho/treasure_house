// 항목 하나를 떼어 처리하고, 남은 것으로 자기를 다시 부른다.
macro_rules! opts_go {
    // 남은 것이 없거나 쉼표 하나뿐이면 끝낸다.
    ($v:ident; $(,)?) => {};
    // 이름 = 값
    ($v:ident; $key:ident = $val:expr, $($rest:tt)*) => {
        $v.push((stringify!($key), $val.to_string()));
        opts_go!($v; $($rest)*);
    };
    // 이름만
    ($v:ident; $key:ident, $($rest:tt)*) => {
        $v.push((stringify!($key), true.to_string()));
        opts_go!($v; $($rest)*);
    };
}

// 부르는 쪽이 쓰는 매크로. 벡터를 만들고 끝에 쉼표를 하나 붙여 넘긴다.
macro_rules! opts {
    ($($all:tt)*) => {{
        let mut v = Vec::new();
        opts_go!(v; $($all)* ,);
        v
    }};
}

fn main() {
    let a = opts!(verbose, level = 3, name = "rs", dry_run);
    println!("{a:?}");
    let b = opts!(quiet, jobs = 2 + 2,);
    println!("{b:?}");
}
