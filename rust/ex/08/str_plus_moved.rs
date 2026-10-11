fn main() {
    let hello = String::from("안녕, ");
    let name = String::from("Ferris");

    let greeting = hello + &name;
    println!("{greeting} {hello}");
}
//@ expect: E0382
