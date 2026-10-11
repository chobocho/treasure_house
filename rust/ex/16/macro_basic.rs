// 패턴 => 펼칠 코드. $x:expr 은 "식 하나를 받아 $x 라고 부른다".
macro_rules! square {
    ($x:expr) => {
        $x * $x
    };
}

fn main() {
    println!("{}", square!(7));
    println!("{}", square!(1.5)); // 타입을 가리지 않는다
}
