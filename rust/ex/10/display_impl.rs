use std::fmt;

#[derive(Debug)]
struct Money {
    won: u64,
}

// Display 는 derive 할 수 없다 — 사람에게 어떻게 보일지는 내가 정한다.
impl fmt::Display for Money {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}원", self.won)
    }
}

fn main() {
    let m = Money { won: 4500 };
    println!("{m} / {m:?}");
    println!("[{m:>10}]"); // 폭·정렬은 따로 구현해야 먹는다
    let text = m.to_string(); // Display 가 있으면 to_string 이 따라온다
    println!("{}", text.len());
}
