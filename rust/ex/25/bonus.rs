// 구간의 점수마다 bonus 를 더한다. 100 을 넘으면 100 으로 한다.
fn add_bonus(scores: &mut [u32], bonus: u32) {
    for s in scores {
        *s += bonus;
        if *s > 100 {
            *s = 100;
        }
    }
}

// line 점 이상인 점수가 몇 개인지 센다
fn count_pass(scores: &[u32], line: u32) -> usize {
    let mut count = 0;
    for s in scores {
        if *s >= line {
            count += 1;
        }
    }
    count
}

fn main() {
    let mut scores = [58, 72, 95, 40, 99];
    println!("{scores:?} 합격 {}명", count_pass(&scores, 60));
    // 뒤의 세 명만 5점을 더 받는다
    add_bonus(&mut scores[2..], 5);
    println!("{scores:?} 합격 {}명", count_pass(&scores, 60));
    // 이번에는 모두 2점을 더 받는다
    add_bonus(&mut scores[..], 2);
    println!("{scores:?} 합격 {}명", count_pass(&scores, 60));
    println!("앞의 둘 가운데 합격 {}명", count_pass(&scores[..2], 60));
}
