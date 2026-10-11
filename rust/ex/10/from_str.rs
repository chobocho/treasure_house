use std::str::FromStr;

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

// FromStr 을 구현하면 "..".parse::<Point>() 가 된다.
impl FromStr for Point {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, String> {
        let (x, y) = s.split_once(',').ok_or("쉼표가 없다")?;
        let x = x.trim().parse().map_err(|_| format!("x: {x}"))?;
        let y = y.trim().parse().map_err(|_| format!("y: {y}"))?;
        Ok(Point { x, y })
    }
}

fn main() {
    println!("{:?}", "3, 4".parse::<Point>());
    println!("{:?}", "3 4".parse::<Point>());
    println!("{:?}", "3, 넷".parse::<Point>());
    println!("{:?}", "3, 4".parse::<Point>().map(|p| p.x + p.y));
}
