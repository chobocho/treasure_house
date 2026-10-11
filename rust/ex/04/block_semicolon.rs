fn main() {
    let area: i32 = {
        let w = 3;
        let h = 4;
        w * h;
    };
    println!("{area}");
}
//@ expect: E0308
