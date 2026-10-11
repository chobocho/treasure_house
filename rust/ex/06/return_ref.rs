// 받은 튜플의 한 칸을 가리키는 참조를 돌려준다
fn longer(pair: &(String, String)) -> &String {
    if pair.0.len() >= pair.1.len() {
        &pair.0
    } else {
        &pair.1
    }
}

fn main() {
    let pair = (String::from("kiwi"), String::from("banana"));
    let l = longer(&pair);
    println!("{l}");
    println!("{pair:?}");
}
