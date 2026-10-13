pub mod spoon;

// 계량컵 하나의 mL. 이 모듈과 그 자식 모듈만 쓴다.
const CUP_ML: u32 = 240;

// 몇 컵인지와 남는 mL.
pub fn cups(ml: u32) -> String {
    format!("{}컵 + {}mL", ml / CUP_ML, ml % CUP_ML)
}
