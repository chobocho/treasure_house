fn parse_pair(s: &str) -> Option<(i32, i32)> {
    // 맞으면 아래에서 계속 쓰고, 안 맞으면 else 에서 빠져나간다.
    let Some((a, b)) = s.split_once(',') else {
        return None;
    };
    let Ok(a) = a.trim().parse::<i32>() else {
        return None;
    };
    let Ok(b) = b.trim().parse::<i32>() else {
        return None;
    };
    Some((a, b))
}

fn main() {
    println!("{:?}", parse_pair("3, 4"));
    println!("{:?}", parse_pair("3 4"));
    println!("{:?}", parse_pair("3, 넷"));
}
