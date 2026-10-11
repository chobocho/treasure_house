// #![feature(...)] 는 불안정한 기능을 켜 달라는 요청이다.
#![feature(never_type)]

fn main() {
    println!("여기까지 오지 못한다");
}
//@ expect: E0554
