fn main() {
    let x = 5;
    // 같은 이름으로 다시 let — 새 변수가 앞의 x 를 가린다
    let x = x + 1;
    {
        // 블록 안에서 가린 것은 블록이 끝나면 풀린다
        let x = x * 2;
        println!("블록 안: {x}");
    }
    println!("블록 밖: {x}");
}
