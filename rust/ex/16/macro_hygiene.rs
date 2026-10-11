macro_rules! double_it {
    ($x:expr) => {{
        let tmp = 2; // 매크로 안의 tmp
        $x * tmp
    }};
}

fn main() {
    let tmp = 10; // 바깥의 tmp
    // 넘긴 식 tmp + 1 의 tmp 는 바깥의 10 이다. 안쪽의 2 가 아니다.
    println!("{}", double_it!(tmp + 1));
    println!("{tmp}");
}
