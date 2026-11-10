// 난수와 7-bag 시험.
use tetris_core::{Bag, Kind, Rng};

fn is_perm(chunk: &[Kind]) -> bool {
    let mut seen = [false; 7];
    for k in chunk {
        seen[k.index()] = true;
    }
    chunk.len() == 7 && seen.iter().all(|&s| s)
}

#[test]
fn seed_zero_is_not_stuck() {
    let mut r = Rng::new(0);
    let a = r.next_u64();
    let b = r.next_u64();
    assert_ne!(a, 0);
    assert_ne!(a, b);
}

#[test]
fn same_seed_same_stream() {
    let mut a = Rng::new(42);
    let mut b = Rng::new(42);
    for _ in 0..100 {
        assert_eq!(a.next_u64(), b.next_u64());
    }
}

#[test]
fn different_seeds_differ() {
    let mut a = Bag::new(1);
    let mut b = Bag::new(2);
    let sa: Vec<Kind> = (0..14).map(|_| a.draw()).collect();
    let sb: Vec<Kind> = (0..14).map(|_| b.draw()).collect();
    assert_ne!(sa, sb);
}

#[test]
fn below_stays_in_range() {
    let mut r = Rng::new(7);
    for n in 1..50 {
        for _ in 0..20 {
            assert!(r.below(n) < n);
        }
    }
    assert_eq!(r.below(1), 0);
}

#[test]
#[should_panic(expected = "n > 0")]
fn below_zero_panics() {
    Rng::new(1).below(0);
}

#[test]
fn every_bag_is_a_permutation() {
    for seed in [0, 1, 99, u64::MAX] {
        let mut bag = Bag::new(seed);
        let seq: Vec<Kind> = (0..70).map(|_| bag.draw()).collect();
        for chunk in seq.chunks(7) {
            assert!(is_perm(chunk), "seed {seed}: {chunk:?}");
        }
    }
}

#[test]
fn peek_shows_what_next_will_return() {
    let mut bag = Bag::new(5);
    for _ in 0..20 {
        let ahead: Vec<Kind> = bag.peek().collect();
        assert!(ahead.len() >= 7, "미리보기는 언제나 7개 이상");
        for want in ahead.iter().take(7) {
            assert_eq!(bag.draw(), *want);
        }
    }
}

#[test]
fn prefix_comes_first_then_full_bags() {
    let pre = [Kind::I, Kind::I, Kind::O];
    let mut bag = Bag::with_prefix(3, &pre);
    let seq: Vec<Kind> = (0..17).map(|_| bag.draw()).collect();
    assert_eq!(&seq[..3], &pre);
    assert!(is_perm(&seq[3..10]));
    assert!(is_perm(&seq[10..17]));
}
