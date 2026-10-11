fn main() {
    let pair = (String::from("left"), String::from("right"));
    let l = pair.0;

    println!("{l}");
    println!("{pair:?}");
}
//@ expect: E0382
