macro_rules! double_it {
    ($x:expr) => {{
        let tmp = $x; // 매크로 안의 tmp
        tmp * 2
    }};
}

fn main() {
    let tmp = 10; // 바깥의 tmp — 이름이 같아도 섞이지 않는다
    println!("{}", double_it!(tmp + 1));
    println!("{tmp}");
}
