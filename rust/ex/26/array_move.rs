fn main() {
    let pair = [String::from("앞"), String::from("뒤")];
    let first = &pair[0];
    println!("{first} {}", pair[1]);
}
