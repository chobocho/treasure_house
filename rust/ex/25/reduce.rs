fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

fn reduce(n: u64, d: u64) -> (u64, u64) {
    let g = gcd(n, d);
    (n / g, d / g)
}

fn show(n: u64, d: u64) {
    let (rn, rd) = reduce(n, d);
    if rd == 1 {
        println!("{n}/{d} = {rn}");
    } else {
        println!("{n}/{d} = {rn}/{rd}");
    }
}

fn main() {
    show(6, 8);
    show(10, 5);
    show(0, 7);
    show(17, 5);
    show(1071, 462);
}
