// tests/ 의 파일은 따로 컴파일되는 크레이트다 — 공개 API 만 쓸 수 있다.
use greeter::greet;

#[test]
fn public_api_works() {
    assert_eq!(greet("kim"), "안녕, kim!");
}
