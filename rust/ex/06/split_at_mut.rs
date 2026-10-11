fn main() {
    let mut v = vec![1, 2, 3];

    // 1번 자리에서 가른다: [1] 과 [2, 3]
    let (left, right) = v.split_at_mut(1);
    println!("{left:?} {right:?}");

    let a = &mut left[0];
    let b = &mut right[0];
    *a += 10;
    *b += 20;
    println!("{v:?}");
}
