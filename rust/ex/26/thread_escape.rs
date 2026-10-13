use std::thread;

fn shout(text: &str) {
    let text = text.to_string();
    let h = thread::spawn(move || println!("{text}!"));
    h.join().unwrap();
}

fn main() {
    shout("안녕");
}
