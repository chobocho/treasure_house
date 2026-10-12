use std::fmt::Display;

// Item 에 조건을 단다 — Display 이기만 하면 된다.
fn print_all<I>(items: I)
where
    I: Iterator,
    I::Item: Display,
{
    for x in items {
        println!("- {x}");
    }
}

// Item 을 한 타입으로 못 박는다 — u32 를 내주는 반복자만.
fn total<I: Iterator<Item = u32>>(items: I) -> u32 {
    let mut sum = 0;
    for x in items {
        sum += x;
    }
    sum
}

fn main() {
    print_all(["a", "b"].iter());
    print_all(1..=2);
    println!("{}", total(vec![10_u32, 20, 30].iter()));
    println!("{}", total((1..=4).map(|x| x * x)));
}
//@ expect: E0271
