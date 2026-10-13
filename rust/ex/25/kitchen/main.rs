mod kitchen;

use kitchen::spoon;

fn main() {
    for ml in [480, 300, 45, 20] {
        println!(
            "{ml:>3}mL = {} = {}",
            kitchen::cups(ml),
            spoon::spoons(ml)
        );
    }
    println!("한 컵은 {}큰술", spoon::per_cup());
}
