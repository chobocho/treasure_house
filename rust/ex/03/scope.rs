fn main() {
    let outer = 1;
    {
        let inner = 2;
        println!("안: {outer} {inner}");
    }
    println!("밖: {outer} {inner}");
}
//@ expect: E0425
