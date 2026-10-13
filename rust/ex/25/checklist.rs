// 조건마다 한 줄씩 찍고, 참인 조건의 수를 값으로 낸다.
macro_rules! check {
    ($($cond:expr),* $(,)?) => {{
        let mut passed = 0;
        $(
            let ok: bool = $cond;
            let mark = if ok { 'v' } else { ' ' };
            println!("[{mark}] {}", stringify!($cond));
            if ok {
                passed += 1;
            }
        )*
        passed
    }};
}

fn main() {
    let age = 17;
    let name = "ferris";
    let passed = 100;

    let n = check!(age >= 14, age >= 19, name.len() <= 8);
    println!("{n}개 통과");

    let n = check!(name == "ferris" && age % 2 == 1, passed == 100,);
    println!("{n}개 통과, 바깥의 passed 는 {passed}");
}
