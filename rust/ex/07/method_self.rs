struct Draft {
    text: String,
}

struct Published {
    text: String,
}

impl Draft {
    // self — 자기를 가져간다. 부르고 나면 원래 값은 없다.
    fn publish(self) -> Published {
        Published { text: self.text }
    }
}

fn main() {
    let d = Draft {
        text: String::from("첫 글"),
    };
    let p = d.publish();
    println!("{}", p.text);
}
