fn main() {
    let names = vec![String::from("kim"), String::from("lee")];
    // move — 빌리지 않고 가져간다. 클로저가 names 의 주인이 된다.
    let show = move || println!("{names:?}");

    show();
    show();
}
