fn main() {
    let mut n = 1;
    {
        let w = &mut n;
        *w += 10;
        println!("블록 안: {w}");
    } // w 는 여기서 사라진다. 빌림도 늦어도 여기까지다.

    let r = &n;
    println!("블록 밖: {r}");
}
