fn main() {
    let a = String::from("tic");
    let b = String::from("tac");
    let c = String::from("toe");

    // 여럿을 이을 때는 format! 이 낫다 — 아무것도 가져가지 않는다.
    let s = format!("{a}-{b}-{c}");
    println!("{s}");
    println!("{a} {b} {c}"); // 전부 그대로 쓸 수 있다

    let parts = [a, b, c];
    println!("{}", parts.join("-")); // 목록이면 join
    println!("{}", parts.concat());
}
