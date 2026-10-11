fn main() {
    let names = vec![String::from("kim"), String::from("lee")];
    let show = move || println!("{names:?}");

    show();
    println!("{names:?}");
}
//@ expect: E0382
