// "09:30" 을 자정부터 센 분으로 바꾼다
fn minutes(clock: &str) -> Result<u32, String> {
    let (h, m) =
        clock.split_once(':').ok_or(String::from("':' 가 없다"))?;
    let h: u32 = h.parse().map_err(|e| format!("수가 아니다: {e}"))?;
    let m: u32 = m.parse().map_err(|e| format!("수가 아니다: {e}"))?;
    if h > 23 || m > 59 {
        return Err(format!("없는 시각 {h}:{m:02}"));
    }
    Ok(h * 60 + m)
}

// "09:30-18:05" 에서 일한 시간을 분으로 돌려준다
fn worked(span: &str) -> Result<u32, String> {
    let (from, to) =
        span.split_once('-').ok_or(String::from("'-' 가 없다"))?;
    let from = minutes(from)?;
    let to = minutes(to)?;
    if to < from {
        return Err(String::from("끝이 시작보다 이르다"));
    }
    Ok(to - from)
}

fn main() {
    let spans = [
        "09:30-18:05",
        "13:00-13:00",
        "9:05-10:00",
        "0930-1805",
        "09:30",
        "09:60-10:00",
        "24:00-25:00",
        "nine:00-10:00",
        "08:00-09:",
        "18:00-09:00",
    ];
    for span in spans {
        match worked(span) {
            Ok(min) => {
                println!("{span} -> {}시간 {}분", min / 60, min % 60)
            }
            Err(why) => println!("{span} -> 오류: {why}"),
        }
    }
}
