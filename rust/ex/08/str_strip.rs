fn main() {
    let line = "port=8080";

    // 앞·뒤의 정해진 글자를 떼어 낸다. 없으면 None.
    println!("{:?}", line.strip_prefix("port="));
    println!("{:?}", line.strip_prefix("host="));
    println!("{:?}", "report.txt".strip_suffix(".txt"));
    println!("{}", "xxhixx".trim_matches('x'));
}
