fn main() {
    // 블록 { } 도 식이다. 마지막 식이 블록의 값이 된다.
    let area = {
        let w = 3;
        let h = 4;
        w * h
    };
    println!("{area}");
}
