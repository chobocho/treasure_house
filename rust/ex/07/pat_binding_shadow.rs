fn main() {
    let target = 5;
    let n = 9;

    let found = match n {
        // 소문자 이름은 "견주기" 가 아니라 "새 변수로 받기" 다.
        target => format!("target 에 {target} 을 받았다"),
    };
    println!("{found}");
    println!("바깥의 target 은 그대로 {target}");
}
