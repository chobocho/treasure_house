fn main() {
    let v = vec![1, 2, 3];
    let it = v.iter().map(|x| x * 2);

    let total: i32 = it.sum();
    let count = it.count();
    println!("{total} {count}");
}
//@ expect: E0382
