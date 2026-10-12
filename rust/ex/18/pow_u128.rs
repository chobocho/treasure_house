fn main() {
    // 체스판 64 칸에 쌀알을 두 배씩 — 마지막 칸은 2 의 63 제곱
    let last = 2_u64.pow(63);
    println!("마지막 칸 {last}");
    println!("u64::MAX  {}", u64::MAX);
    // 한 칸만 더 가도 u64 를 넘는다
    println!("checked   {:?}", 2_u64.checked_pow(64));
    // u128 은 128 비트 — 같은 셈이 들어간다
    let next = 2_u128.pow(64);
    println!("u128      {next}");
    println!("전체 합   {}", next - 1);
    println!("u128::MAX {}", u128::MAX);
    println!("i128::MIN {}", i128::MIN);
    // 좁히는 as 는 다른 정수 타입에서처럼 아래 비트만 남긴다
    let big: u128 = (1 << 100) + 7;
    println!("big       {big}");
    println!("as u64    {}", big as u64);
}
