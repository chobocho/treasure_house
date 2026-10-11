// 매개변수는 그 함수의 지역 변수다. mut 를 붙이면 안에서 고칠 수 있다.
fn countdown(mut n: u32) {
    while n > 0 {
        print!("{n} ");
        n -= 1;
    }
    println!("발사");
}

fn main() {
    let start = 3;
    countdown(start);
    println!("start 는 그대로 {start}");
}
