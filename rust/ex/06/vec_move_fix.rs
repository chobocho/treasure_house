fn main() {
    // Copy 타입의 칸은 대입하면 복사된다. 막힐 것이 없다.
    let nums = vec![10, 20];
    let n = nums[0];
    println!("{n} {nums:?}");

    let mut names = vec![
        String::from("kim"),
        String::from("lee"),
        String::from("park"),
    ];
    // 1. 복사본을 만든다
    let copy = names[0].clone();
    // 2. 옮기지 않고 빌려서 본다 (3장)
    let look = &names[1];
    println!("{copy} {look}");

    // 3. 꺼낸다. 벡터에서는 그 칸이 빠진다.
    let taken = names.remove(0);
    println!("{taken} {names:?}");

    // 4. 벡터를 통째로 넘겨 하나씩 받는다
    for name in names {
        println!("{name}");
    }
}
