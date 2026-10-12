// 한도가 없으면 통과, 있으면 그 안이어야 한다
fn allowed(size: u32, limit: Option<u32>) -> bool {
    limit.is_none_or(|max| size <= max)
}

// 없으면 까닭을 붙여 Err 로 바꾼다
fn need(who: Option<&str>) -> Result<&str, String> {
    who.ok_or_else(|| {
        println!("  (오류 글을 만든다)");
        String::from("이름이 없다")
    })
}

fn main() {
    let name: Option<&str> = Some("kim");
    let nobody: Option<&str> = None;

    // map_or — 있으면 바꾸고, 없으면 기본값. 결과는 Option 이 아니다
    println!("{}", name.map_or(0, |s| s.len()));
    println!("{}", nobody.map_or(0, |s| s.len()));
    // map 과 unwrap_or 를 이어 적은 것과 같은 답이다
    println!("{}", nobody.map(|s| s.len()).unwrap_or(0));

    // is_none_or 와 is_some_and — None 일 때의 답이 반대다
    println!("{} {}", allowed(80, Some(100)), allowed(120, Some(100)));
    println!("{}", allowed(120, None));
    println!("{}", None::<u32>.is_some_and(|max| 120 <= max));

    // ok_or_else — 없을 때만 오류 값을 만든다
    println!("{:?}", need(name));
    println!("{:?}", need(nobody));
}
