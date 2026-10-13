use std::collections::VecDeque;

// 한 번에 일하는 시간(분)
const SLICE: u32 = 3;

fn main() {
    let mut queue = VecDeque::new();
    queue.push_back(("print", 5));
    queue.push_back(("scan", 2));
    queue.push_back(("copy", 6));
    let mut clock = 0;
    while let Some((name, left)) = queue.pop_front() {
        if left > SLICE {
            clock += SLICE;
            queue.push_back((name, left - SLICE));
            println!(
                "{clock:>2}분 {name} 줄 뒤로, 남은 일 {}분",
                left - SLICE
            );
        } else {
            clock += left;
            println!("{clock:>2}분 {name} 끝");
        }
    }
}
