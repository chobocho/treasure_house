/// 인자들을 이어 큰 글자로 만든다. 인자가 없으면 쓰는 법을 Err 로 준다.
pub fn run(args: &[String]) -> Result<String, String> {
    if args.is_empty() {
        return Err(String::from("쓰는 법: shout <낱말>..."));
    }
    Ok(format!("{}!", args.join(" ").to_uppercase()))
}
