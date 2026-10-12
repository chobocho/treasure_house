fn main() {
    // get_or_insert_with — 비어 있을 때만 만들어 넣고, 속을 빌려준다
    let mut cache: Option<u64> = None;
    for _ in 0..2 {
        let total = cache.get_or_insert_with(|| {
            println!("  (합을 구한다)");
            (1..=100).sum()
        });
        println!("{total}");
    }
    println!("{cache:?}");

    // 돌려받은 것은 가변 참조다 — 속을 고칠 수 있다
    *cache.get_or_insert(0) += 1;
    println!("{cache:?}");

    // replace — 새 값을 넣고, 있던 것을 돌려받는다
    let mut best: Option<u32> = None;
    let old = best.replace(72);
    println!("{old:?} {best:?}");
    let old = best.replace(91);
    println!("{old:?} {best:?}");

    // take — 꺼내고 None 을 남긴다
    let old = best.take();
    println!("{old:?} {best:?}");
}
