use shop_core::total;

fn main() {
    println!("{}", total(&[12_000, 9_500]));
    println!("{}", total(&[12_000, 9_500, 8_500]));
}
