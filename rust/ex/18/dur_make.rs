use std::time::Duration;

fn main() {
    // 길이를 만든다 — 단위는 함수 이름에 있다
    let boil = Duration::from_secs(90);
    let blink = Duration::from_millis(250);
    let half = Duration::from_secs_f64(1.5);
    println!("{boil:?} {blink:?} {half:?}");

    // 다른 단위로 만들어도 길이가 같으면 같은 값이다
    println!("{}", Duration::from_millis(1500) == half);
    println!("{}", Duration::from_secs(1) == half);

    // 꺼낼 때도 단위를 고른다
    let lap = Duration::from_millis(2750);
    println!("{}", lap.as_secs());
    println!("{}", lap.as_millis());
    println!("{}", lap.as_secs_f64());
    // 초를 떼고 남은 조각
    println!("{} 초 + {} 밀리초", lap.as_secs(), lap.subsec_millis());

    // 초와 나노초로 만드는 길도 있다
    println!("{}", Duration::new(2, 750_000_000) == lap);
    println!("{:?}", Duration::ZERO);
}
