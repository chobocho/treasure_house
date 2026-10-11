struct Draft {
    text: String,
}

impl Draft {
    fn publish(self) -> String {
        self.text
    }
}

fn main() {
    let d = Draft {
        text: String::from("첫 글"),
    };
    let a = d.publish();
    let b = d.publish();
    println!("{a} {b}");
}
//@ expect: E0382
