//! 의사 난수와 7-bag.
//!
//! `rand` 크레이트를 쓰지 않는다. WASM 에는 OS 난수원이 없고,
//! 같은 씨앗에서 같은 판이 나와야 시험·녹화가 재현되기 때문이다.

use crate::piece::Kind;
use std::collections::VecDeque;

// ANCHOR: rng
/// xorshift64* — 상태 8바이트, 곱셈 한 번. 게임용으로 충분하다.
#[derive(Clone, Debug)]
pub struct Rng {
    state: u64,
}

impl Rng {
    pub fn new(seed: u64) -> Rng {
        // splitmix64 로 씨앗을 한 번 섞는다. 0·1·2 처럼 비슷한 씨앗도
        // 전혀 다른 수열이 되고, xorshift 가 갇히는 상태 0 을 피한다.
        let mut z = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^= z >> 31;
        Rng {
            state: if z == 0 { 1 } else { z },
        }
    }

    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    /// 0 이상 n 미만. 상위 32비트에 n 을 곱해 자른다(나눗셈 없음).
    /// 편향은 n/2³² 이하 — n ≤ 7 인 이 게임에서는 무시해도 된다.
    pub fn below(&mut self, n: u32) -> u32 {
        assert!(n > 0, "below(n) 는 n > 0 이어야 한다");
        (((self.next_u64() >> 32) * n as u64) >> 32) as u32
    }
}
// ANCHOR_END: rng

// ANCHOR: bag
/// 일곱 조각을 한 봉지에 넣고 섞어 차례로 꺼낸다. 같은 조각이
/// 오래 안 나오는 "가뭄"이 최대 12개로 묶인다.
#[derive(Clone, Debug)]
pub struct Bag {
    rng: Rng,
    queue: VecDeque<Kind>,
}

impl Bag {
    pub fn new(seed: u64) -> Bag {
        Bag::with_prefix(seed, &[])
    }

    /// `prefix` 를 먼저 내놓고 그다음부터 봉지. 시험에서 첫 조각을
    /// 정해 두는 데 쓴다.
    pub fn with_prefix(seed: u64, prefix: &[Kind]) -> Bag {
        let mut bag = Bag {
            rng: Rng::new(seed),
            queue: prefix.iter().copied().collect(),
        };
        bag.refill();
        bag
    }
    // ANCHOR_END: bag

    // ANCHOR: bag_draw
    /// 미리보기가 모자라지 않도록 큐를 언제나 7개 이상으로 유지한다.
    fn refill(&mut self) {
        while self.queue.len() < 7 {
            let mut b = Kind::ALL;
            // 피셔–예이츠 셔플: O(n), 모든 순열이 같은 확률
            for i in (1..b.len()).rev() {
                let j = self.rng.below(i as u32 + 1) as usize;
                b.swap(i, j);
            }
            self.queue.extend(b);
        }
    }

    pub fn draw(&mut self) -> Kind {
        let k = self.queue.pop_front().expect("refill 이 큐를 채운다");
        self.refill();
        k
    }

    /// 다음에 나올 조각들(7개 이상). `&self` 라서 꺼내지 않고
    /// 보기만 한다.
    pub fn peek(&self) -> impl Iterator<Item = Kind> + '_ {
        self.queue.iter().copied()
    }
    // ANCHOR_END: bag_draw
}
