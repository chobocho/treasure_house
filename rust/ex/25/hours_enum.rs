use std::fmt;
use std::num::ParseIntError;

enum TimeError {
    Missing(char),
    Number(ParseIntError),
    NoSuchTime(u32, u32),
    Backwards,
}

impl fmt::Display for TimeError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            TimeError::Missing(c) => write!(f, "'{c}' 가 없다"),
            TimeError::Number(e) => write!(f, "수가 아니다: {e}"),
            TimeError::NoSuchTime(h, m) => {
                write!(f, "없는 시각 {h}:{m:02}")
            }
            TimeError::Backwards => write!(f, "끝이 시작보다 이르다"),
        }
    }
}

impl From<ParseIntError> for TimeError {
    fn from(e: ParseIntError) -> Self {
        TimeError::Number(e)
    }
}

fn minutes(clock: &str) -> Result<u32, TimeError> {
    let (h, m) =
        clock.split_once(':').ok_or(TimeError::Missing(':'))?;
    let h: u32 = h.parse()?;
    let m: u32 = m.parse()?;
    if h > 23 || m > 59 {
        return Err(TimeError::NoSuchTime(h, m));
    }
    Ok(h * 60 + m)
}

fn worked(span: &str) -> Result<u32, TimeError> {
    let (from, to) =
        span.split_once('-').ok_or(TimeError::Missing('-'))?;
    let from = minutes(from)?;
    let to = minutes(to)?;
    if to < from {
        return Err(TimeError::Backwards);
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
