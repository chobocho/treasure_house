fn main() {
    let names = [String::from("a"), String::from("b")];
    // 2021 부터: 값(String)을 꺼내 준다 — 배열은 소비된다.
    for n in names.into_iter() {
        let _: String = n;
    }
    println!("{:?}", names);
}
//@ edition: 2021
//@ expect: E0382
