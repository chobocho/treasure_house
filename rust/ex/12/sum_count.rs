fn main() {
    let v = [3, 1, 4, 1, 5];

    let total: i32 = v.iter().sum();
    let product: i32 = v.iter().product();
    let ones = v.iter().filter(|x| **x == 1).count();
    println!("{total} {product} {ones}");
    println!("{:?} {:?}", v.iter().min(), v.iter().max());
    println!("{:?} {:?}", v.iter().last(), v.iter().nth(2));
}
