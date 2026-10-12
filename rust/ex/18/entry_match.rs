use std::collections::HashMap;
use std::collections::hash_map::Entry;

type Lent = HashMap<&'static str, u32>;

fn lend(lent: &mut Lent, title: &'static str) {
    match lent.entry(title) {
        // 빈 자리 — insert 로 채운다
        Entry::Vacant(slot) => {
            slot.insert(1);
            println!("{title}: 처음 나간다");
        }
        // 찬 자리 — get_mut 으로 고친다
        Entry::Occupied(mut slot) => {
            *slot.get_mut() += 1;
            println!("{title}: {} 권째 나간다", slot.get());
        }
    }
}

fn give_back(lent: &mut Lent, title: &'static str) {
    match lent.entry(title) {
        Entry::Vacant(_) => println!("{title}: 나간 적이 없다"),
        Entry::Occupied(mut slot) => {
            *slot.get_mut() -= 1;
            // 0 이 되면 항목을 지운다
            if *slot.get() == 0 {
                slot.remove();
                println!("{title}: 모두 돌아왔다");
            } else {
                println!("{title}: {} 권 남았다", slot.get());
            }
        }
    }
}

fn main() {
    let mut lent = Lent::new();
    lend(&mut lent, "러스트");
    lend(&mut lent, "러스트");
    give_back(&mut lent, "러스트");
    give_back(&mut lent, "러스트");
    give_back(&mut lent, "러스트");
    println!("{}", lent.len());
}
