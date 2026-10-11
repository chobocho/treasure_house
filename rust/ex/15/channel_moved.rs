use std::sync::mpsc;

fn main() {
    let (tx, rx) = mpsc::channel();
    let msg = String::from("안녕");
    tx.send(msg).unwrap();
    println!("보낸 뒤: {msg}");
    println!("{}", rx.recv().unwrap());
}
//@ expect: E0382
