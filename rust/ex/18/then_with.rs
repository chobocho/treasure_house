use std::cmp::Ordering;

struct Person {
    name: &'static str,
    age: u32,
}

// 이름순, 이름이 같으면 나이순
fn by_name_age(a: &Person, b: &Person) -> Ordering {
    a.name.cmp(b.name).then_with(|| a.age.cmp(&b.age))
}

fn main() {
    let p = |name, age| Person { name, age };
    let mut people =
        vec![p("lee", 40), p("kim", 30), p("park", 22), p("kim", 25)];
    people.sort_by(by_name_age);
    for x in &people {
        println!("{} {}", x.name, x.age);
    }

    // then_with 의 클로저는 앞의 결과가 Equal 일 때만 불린다
    let second = || {
        println!("  (둘째 기준을 견준다)");
        Ordering::Greater
    };
    println!("{:?}", Ordering::Less.then_with(second));
    println!("{:?}", Ordering::Equal.then_with(second));
    // then 은 클로저가 아니라 이미 셈한 값을 받는다
    println!("{:?}", Ordering::Equal.then(Ordering::Less));
}
