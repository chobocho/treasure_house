fn main() {
    let rolls = [3, 6, 1, 3, 5, 3, 6, 2, 6, 3, 1, 6];
    // 0번 칸은 비워 두고 1번부터 6번 칸에 센다
    let mut counts = [0; 7];
    for r in rolls {
        counts[r] += 1;
    }
    let mut best = 1;
    for face in 1..=6 {
        let n = counts[face];
        if n == 0 {
            continue;
        }
        print!("{face}: ");
        for _step in 0..n {
            print!("#");
        }
        println!(" {n}");
        // 같으면 바꾸지 않으므로 작은 눈이 남는다
        if n > counts[best] {
            best = face;
        }
    }
    println!("가장 많이 나온 눈 {best}");
}
