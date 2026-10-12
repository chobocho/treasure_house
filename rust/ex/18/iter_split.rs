fn main() {
    let scores = [("kim", 72), ("lee", 48), ("park", 91), ("choi", 55)];

    // partition — 조건이 참인 것과 거짓인 것으로 가른다
    let (pass, fail): (Vec<_>, Vec<_>) =
        scores.iter().copied().partition(|(_, score)| *score >= 60);
    println!("{pass:?}");
    println!("{fail:?}");

    // unzip — 짝의 반복자를 벡터 둘로 푼다
    let (names, points): (Vec<&str>, Vec<u32>) =
        scores.iter().copied().unzip();
    println!("{names:?}");
    println!("{points:?}");

    // zip 을 두 번 이으면 셋이 한 줄에 선다
    let grades = ['C', 'F', 'A', 'F'];
    for ((name, point), grade) in names.iter().zip(&points).zip(grades)
    {
        println!("{name:5} {point:3} {grade}");
    }
}
