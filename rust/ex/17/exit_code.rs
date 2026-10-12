use std::process::ExitCode;

struct Temp(&'static str);

impl Drop for Temp {
    fn drop(&mut self) {
        println!("{} 정리", self.0);
    }
}

fn main() -> ExitCode {
    let _t = Temp("임시 자료");
    println!("일하다가 문제를 만났다");
    // main 이 평소처럼 돌아가며 종료 코드만 정한다
    ExitCode::from(2)
}
//@ exit: 2
