fn main() {
    for score in [72, 48] {
        let grade;
        if score >= 60 {
            grade = "합격";
        }
        println!("{score}점: {grade}");
    }
}
//@ expect: E0381
