fn main() {
    let score = 72;
    let result: &str = if score >= 60 {
        "합격"
    };
    println!("{result}");
}
//@ expect: E0317
