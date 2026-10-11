fn main() {
    let mut names = vec![String::from("kim"), String::from("lee")];

    let first: &String = &names[0]; // 빌린다
    println!("{first}");
    let copy: String = names[0].clone(); // 복사한다
    let taken: String = names.remove(0); // 꺼내 간다
    println!("{copy} {taken} {names:?}");
    // 맨 끝을 꺼내려면 pop.
    println!("{:?}", names.pop());
}
