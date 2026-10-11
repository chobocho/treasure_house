fn main() {
    let mut total = 0;
    // 주변 변수를 고친다 — 가변으로 빌린다.
    // 클로저를 담은 변수도 mut 여야 한다.
    let mut add = |n: i32| total += n;

    add(10);
    add(5);
    println!("{total}");
}
