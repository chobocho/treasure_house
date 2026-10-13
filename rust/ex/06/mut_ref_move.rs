fn main() {
    let mut n = 1;
    let m = &mut n;
    // 가변 참조를 같은 꼴로 대입한다
    let m2 = m;
    *m2 += 1;
    *m += 1;
    println!("{n}");
}
//@ expect: E0382
