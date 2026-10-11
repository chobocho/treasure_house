fn main() {
    let names = [String::from("a"), String::from("b")];
    // 2018 까지: 배열의 into_iter() 는 참조(&String)를 돌려준다.
    for n in names.into_iter() {
        let _: &String = n;
    }
    println!("배열은 아직 살아 있다: {:?}", names);
}
//@ edition: 2018
//@ warnings: show
