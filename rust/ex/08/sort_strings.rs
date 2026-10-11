fn main() {
    let mut words = vec!["banana", "apple", "Cherry", "fig"];

    words.sort(); // 바이트 순서 — 대문자가 먼저
    println!("{words:?}");
    words.sort_by_key(|w| w.to_lowercase()); // 대소문자를 가리지 않고
    println!("{words:?}");
    words.sort_by_key(|w| w.len()); // 길이순
    println!("{words:?}");

    let mut names = vec!["다람쥐", "가재", "나비"];
    names.sort();
    println!("{names:?}");
}
