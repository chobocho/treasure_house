use std::num::ParseIntError;

// 모두 수일 때만 합이 나온다
fn total(items: &[&str]) -> Result<i32, ParseIntError> {
    items
        .iter()
        .map(|s| {
            println!("  읽는다 {s}");
            s.parse::<i32>()
        })
        .sum()
}

fn main() {
    println!("{:?}", total(&["3", "4", "5"]));
    println!("{:?}", total(&["3", "넷", "5"]));

    // Option 도 같은 식으로 더한다
    let full = [Some(2), Some(3), Some(4)];
    let hole = [Some(2), None, Some(4)];
    println!("{:?}", full.into_iter().sum::<Option<i32>>());
    println!("{:?}", hole.into_iter().sum::<Option<i32>>());
    println!("{:?}", full.into_iter().product::<Option<i32>>());

    // try_fold — 접다가 None 이 나오면 거기서 멈춘다
    let add = |acc: u8, x: &u8| {
        println!("  {acc} + {x}");
        acc.checked_add(*x)
    };
    println!("{:?}", [100, 100, 50].iter().try_fold(0_u8, add));
    println!("{:?}", [100, 100, 100, 7].iter().try_fold(0_u8, add));
}
