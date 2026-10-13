// 정렬된 정류장 가운데 pos 에서 가장 가까운 것과 거기까지의 거리.
// 거리가 같으면 앞의 정류장이다. 정류장이 없으면 None.
fn nearest(stops: &[u32], pos: u32) -> Option<(u32, u32)> {
    // 있으면 그 자리, 없으면 끼워 넣을 자리.
    let i = match stops.binary_search(&pos) {
        Ok(i) => i,
        Err(i) => i,
    };
    // 가까울 수 있는 것은 그 자리의 앞 칸과 그 칸뿐이다.
    let from = if i > 0 { i - 1 } else { 0 };
    let near = stops[from..].iter().take(2);
    let stop = near.min_by_key(|stop| pos.abs_diff(**stop))?;
    Some((*stop, pos.abs_diff(*stop)))
}

fn report(stops: &[u32], pos: u32) {
    match nearest(stops, pos) {
        Some((stop, far)) => println!("{pos:>4}: {stop} 까지 {far}"),
        None => println!("{pos:>4}: 정류장이 없다"),
    }
}

fn main() {
    let stops = [120, 340, 560, 910];
    for pos in [0, 340, 400, 450, 500, 1000] {
        report(&stops, pos);
    }
    report(&[], 5);
}
