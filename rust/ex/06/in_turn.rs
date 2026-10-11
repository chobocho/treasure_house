fn main() {
    let mut s = String::from("a");

    let w1 = &mut s;
    w1.push('b'); // w1 을 마지막으로 쓴다
    let w2 = &mut s; // 그래서 두 번째 &mut 가 된다
    w2.push('c');

    let r = &s; // &mut 가 끝났으니 & 도 된다
    println!("{r}");

    s = String::from("new"); // 대입도
    let t = s; // 이동도 된다
    println!("{t}");
}
