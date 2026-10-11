fn main() {
    for i in (1..=3).rev() {
        print!("{i} ");
    }
    println!("발사");
    for i in (0..10).step_by(3) {
        print!("{i} ");
    }
    println!();
}
