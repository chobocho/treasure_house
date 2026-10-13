fn main() {
    let names = vec![String::from("가람"), String::from("나래")];
    for name in names {
        println!("{name}");
    }
    println!("{}명", names.len());
}
//@ expect: E0382
