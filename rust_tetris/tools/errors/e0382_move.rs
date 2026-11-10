// Java·Python 이라면 두 변수가 같은 리스트를 가리킬 뿐이다.
fn main() {
    let queue = vec!['T', 'S', 'Z'];
    let other = queue; // 소유권이 other 로 "이동"한다
    println!("{:?}", queue);
    println!("{:?}", other);
}
