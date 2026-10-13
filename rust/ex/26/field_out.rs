struct Member {
    name: String,
}

impl Member {
    fn name(&self) -> &str {
        &self.name
    }
}

fn main() {
    let m = Member {
        name: String::from("가람"),
    };
    println!("{}", m.name());
}
