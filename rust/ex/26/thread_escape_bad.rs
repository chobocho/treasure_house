use std::thread;

fn shout(text: &str) {
    let h = thread::spawn(move || println!("{text}!"));
    h.join().unwrap();
}

fn main() {
    shout("안녕");
}
//@ expect: E0521
