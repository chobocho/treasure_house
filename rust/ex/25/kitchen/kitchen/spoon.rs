const SPOON_ML: u32 = 15;

// 몇 큰술인지와 남는 mL.
pub fn spoons(ml: u32) -> String {
    format!("{}큰술 + {}mL", ml / SPOON_ML, ml % SPOON_ML)
}

// 부모 모듈의 비공개 상수를 쓴다.
pub fn per_cup() -> u32 {
    super::CUP_ML / SPOON_ML
}
