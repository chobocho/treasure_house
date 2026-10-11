fn main() {
    let a: Vec<i32> = Vec::new(); // 빈 벡터 — 원소 타입을 적어 준다
    let b = vec![1, 2, 3];
    let c = vec![0; 5]; // 0 을 다섯 개
    let d: Vec<u32> = (1..=4).collect();
    let e = Vec::from([10, 20]);

    println!("{a:?} {b:?} {c:?} {d:?} {e:?}");
}
