use std::ops::Index;

struct Week {
    hours: [u32; 7],
}

// [] 는 Index 트레이트다. 문자열로도 색인하게 만들 수 있다.
impl Index<&str> for Week {
    type Output = u32;

    fn index(&self, day: &str) -> &u32 {
        let i = ["월", "화", "수", "목", "금", "토", "일"]
            .iter()
            .position(|d| *d == day)
            .expect("요일 이름이 아니다");
        &self.hours[i]
    }
}

fn main() {
    let w = Week {
        hours: [8, 8, 6, 8, 4, 0, 0],
    };
    println!("{} {}", w["월"], w["금"]);
}
