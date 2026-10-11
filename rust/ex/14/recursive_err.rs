// 목록 = 값 하나 + 나머지 목록. 자기 안에 자기가 들어 있다.
enum List {
    Cons(i32, List),
    Nil,
}

fn main() {
    let _list = List::Cons(1, List::Nil);
}
//@ expect: E0072
