// 칸이 N 개인 고리 버퍼. 다 차면 처음 칸부터 덮어쓴다.
struct Ring<const N: usize> {
    slots: [u8; N],
    next: usize,
}

impl<const N: usize> Ring<N> {
    fn new() -> Ring<N> {
        Ring {
            slots: [0; N],
            next: 0,
        }
    }

    fn push(&mut self, value: u8) {
        self.slots[self.next % N] = value;
        self.next += 1;
    }
}

fn main() {
    let mut ring: Ring<3> = Ring::new();
    // 칸이 없는 고리를 만들려 한다.
    let mut empty: Ring<0> = Ring::new();
    empty.push(9);
    for v in 1..=4 {
        ring.push(v);
    }
    println!("{:?}", ring.slots);
}
//@ exit: 101
