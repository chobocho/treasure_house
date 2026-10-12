/// 켜진 기능에 따라 글을 꾸민다.
pub fn shout(s: &str) -> String {
    let mut out = s.to_string();
    if cfg!(feature = "upper") {
        out = out.to_uppercase();
    }
    if cfg!(feature = "mark") {
        out.push('!');
    }
    out
}
