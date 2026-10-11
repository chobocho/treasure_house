fn add_one(x: &mut i32) {
    *x += 1;
}

fn add_two(x: &mut i32) {
    // 받은 참조를 아래 함수에 그대로 넘긴다
    add_one(x);
    add_one(x);
}

fn main() {
    let mut n = 0;
    add_two(&mut n);
    add_two(&mut n);
    println!("{n}");
}
