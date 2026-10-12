use std::sync::mpsc::{self, Sender};
use std::thread;

// 요청은 답을 받을 채널의 보내는 쪽을 들고 간다.
struct Request {
    text: String,
    reply: Sender<usize>,
}

fn main() {
    let (req_tx, req_rx) = mpsc::channel::<Request>();

    let server = thread::spawn(move || {
        let mut served = 0;
        for req in req_rx {
            let words = req.text.split_whitespace().count();
            req.reply.send(words).unwrap(); // 물은 쪽에게만
            served += 1;
        }
        served
    });

    let clients: Vec<_> = ["a b c", "hello world"]
        .into_iter()
        .map(|text| {
            let req_tx = req_tx.clone();
            thread::spawn(move || {
                let (reply, answer) = mpsc::channel();
                let text = text.to_string();
                req_tx.send(Request { text, reply }).unwrap();
                answer.recv().unwrap()
            })
        })
        .collect();
    drop(req_tx);

    for c in clients {
        println!("낱말 수: {}", c.join().unwrap());
    }
    println!("처리한 요청: {}", server.join().unwrap());
}
