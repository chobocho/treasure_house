fn main() {
    let x = 5; // 가리킬 값을 더 오래 살게 한다
    let r;
    {
        r = &x;
    }
    println!("{r}");
}
