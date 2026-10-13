// job 을 1번째부터 times 번째까지 부른다.
// Ok 가 나오면 거기서 멈추고, 마지막으로 받은 것을 돌려준다.
fn retry(
    times: u32,
    mut job: impl FnMut(u32) -> Result<u32, String>,
) -> Result<u32, String> {
    let mut last = Err(String::from("한 번도 부르지 않았다"));
    for nth in 1..=times {
        last = job(nth);
        if last.is_ok() {
            break;
        }
    }
    last
}

// first 번째보다 앞에서는 실패하고, 그 뒤로는 번호의 100 배를 준다.
fn ok_from(first: u32) -> impl Fn(u32) -> Result<u32, String> {
    move |nth| {
        if nth < first {
            Err(format!("{nth}번째 실패"))
        } else {
            Ok(nth * 100)
        }
    }
}

fn main() {
    println!("{:?}", retry(5, ok_from(3)));
    println!("{:?}", retry(2, ok_from(3)));
    println!("{:?}", retry(0, ok_from(1)));

    let mut calls = Vec::new();
    let got = retry(4, |nth| {
        calls.push(nth);
        if nth % 2 == 0 {
            Ok(nth)
        } else {
            Err(String::from("홀수"))
        }
    });
    println!("{got:?} {calls:?}");
}
