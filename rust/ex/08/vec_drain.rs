fn main() {
    let mut queue = vec!["a", "b", "c", "d", "e"];

    // drain — 범위를 떼어 내 반복자로 준다. 벡터에서는 사라진다.
    let batch: Vec<&str> = queue.drain(..2).collect();
    println!("{batch:?} {queue:?}");

    let tail = queue.split_off(1); // 자리 1 부터를 새 벡터로
    println!("{queue:?} {tail:?}");
}
