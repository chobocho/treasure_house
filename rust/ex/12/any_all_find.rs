fn main() {
    let v = [4, 8, 15, 16];

    println!("{}", v.iter().any(|x| x % 2 == 1)); // 하나라도
    println!("{}", v.iter().all(|x| *x > 3)); // 전부
    println!("{:?}", v.iter().find(|x| **x > 10)); // 처음 맞는 원소
    println!("{:?}", v.iter().position(|x| *x > 10)); // 그 자리
    println!("{:?}", v.iter().find(|x| **x > 100));
}
