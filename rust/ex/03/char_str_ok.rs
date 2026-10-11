use std::any::type_name_of_val;

fn main() {
    let grade = 'A';
    let label = "A";
    println!("{grade} ({})", type_name_of_val(&grade));
    println!("{label} ({})", type_name_of_val(&label));
}
