mod tank {
    // 물탱크. level 은 늘 0 부터 100 까지다.
    pub struct Tank {
        level: u32,
    }

    impl Tank {
        pub fn new() -> Tank {
            Tank { level: 0 }
        }

        // 물을 붓는다. 100 을 넘는 물은 넘쳐서 버려진다.
        pub fn fill(&mut self, liters: u32) {
            self.level = (self.level + liters).min(100);
        }
    }
}

fn main() {
    let mut t = tank::Tank::new();
    for liters in [30, 50, 40] {
        t.fill(liters);
        println!("{liters} 을 부어 {:>3}", t.level);
    }
}
//@ expect: E0616
