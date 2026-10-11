fn take_name(name: &mut String) -> String {
    // 값을 꺼내고 그 자리에는 빈 String 을 둔다
    std::mem::take(name)
}

fn main() {
    let mut name = String::from("kim");
    let old = take_name(&mut name);
    println!("[{old}] [{name}]");

    // 벡터에서는 빈 벡터가 남는다
    let mut v = vec![1, 2, 3];
    let got = std::mem::take(&mut v);
    println!("{got:?} {v:?}");
}
