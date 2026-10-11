fn main() {
    // 이름만 먼저 만든다 — 값은 아직 없다
    let total;
    {
        let price = 300;
        let count = 4;
        total = price * count;
    }
    // 블록은 끝났지만 total 은 바깥의 이름이라 남아 있다
    println!("합계: {total}");
}
