fn main() {
    let r;
    {
        let x = 5;
        r = &x; // x 를 빌린다
    } // x 는 여기서 사라진다
    println!("{r}"); // 사라진 x 를 가리키는 참조를 쓴다
}
//@ expect: E0597
