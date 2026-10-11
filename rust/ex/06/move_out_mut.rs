// 이름을 꺼내서 돌려주고 싶다
fn take_name(name: &mut String) -> String {
    *name
}

fn main() {
    let mut name = String::from("kim");
    let old = take_name(&mut name);
    println!("[{old}] [{name}]");
}
//@ expect: E0507
