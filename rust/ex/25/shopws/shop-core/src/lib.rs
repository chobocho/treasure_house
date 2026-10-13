/// 값들의 합에 배송비 3000 을 더한다. 합이 30000 이상이면 그대로다.
pub fn total(prices: &[u32]) -> u32 {
    let sum: u32 = prices.iter().sum();
    if sum >= 30_000 { sum } else { sum + 3_000 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shipping_is_free_from_30000() {
        assert_eq!(total(&[29_999]), 32_999);
        assert_eq!(total(&[30_000]), 30_000);
    }
}
