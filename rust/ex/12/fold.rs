fn main() {
    let v = [3, 1, 4];

    // fold(처음 값, |지금까지, 이번 것| 다음 값)
    let total = v.iter().fold(0, |acc, x| acc + x);
    let text = v.iter().fold(String::new(), |mut acc, x| {
        if !acc.is_empty() {
            acc.push('-');
        }
        acc.push_str(&x.to_string());
        acc
    });
    println!("{total} {text}");
}
