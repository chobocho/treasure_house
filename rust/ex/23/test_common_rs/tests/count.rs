// 같은 디렉터리의 common/mod.rs 를 모듈로 끌어온다.
mod common;

#[test]
fn counts_four() {
    assert_eq!(wordbox::count(&common::sample()), 4);
}
