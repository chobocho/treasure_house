fn main() {
    let names = [String::from("a"), String::from("b")];
    // 에디션에 따라 n 이 참조(&String)이기도, 값(String)이기도 하다.
    for n in names.into_iter() {
        let _: &String = n;
    }
    println!("{:?}", names);
}
//@ edition: 2018
//@ warnings: show
