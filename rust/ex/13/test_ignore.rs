#[test]
fn quick() {
    assert_eq!(2 + 2, 4);
}

// 평소에는 건너뛰는 시험. --ignored 를 주면 돈다.
#[test]
#[ignore]
fn slow() {
    let total: u64 = (1..=10_000_000u64).sum();
    assert_eq!(total, 50_000_005_000_000);
}
//@ test
