use std::time::Duration;

fn main() {
    let song = Duration::from_secs(215);
    let gap = Duration::from_millis(1500);

    // 길이끼리 더하고 뺀다
    println!("{:?}", song + gap);
    println!("{:?}", song - gap);
    // 수를 곱하고 수로 나눈다
    println!("{:?} {:?}", gap * 4, song / 2);

    // 길이끼리 견준다
    println!("{} {}", gap < song, song.max(gap) == song);

    // 노래 세 곡, 그리고 그 사이의 틈 둘
    let secs = [215_u64, 172, 242];
    let songs: Vec<Duration> =
        secs.iter().map(|s| Duration::from_secs(*s)).collect();
    let mut total: Duration = songs.iter().sum();
    println!("{total:?}");
    total += gap * 2;
    println!("{total:?}");

    // 가장 긴 곡, 그리고 3 분을 넘는 곡의 수
    let three_min = Duration::from_secs(180);
    println!("{:?}", songs.iter().max());
    println!("{}", songs.iter().filter(|s| **s > three_min).count());
}
