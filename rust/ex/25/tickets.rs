use std::sync::{Arc, Mutex};
use std::thread;

// 표 stock 장을 창구들이 나눠 판다. wants 는 창구마다 팔려는 장수다.
// (판 장수의 합, 남은 장수) 를 돌려준다.
fn sell(stock: u32, wants: &[u32]) -> (u32, u32) {
    let left = Arc::new(Mutex::new(stock));
    let mut handles = Vec::new();
    for &want in wants {
        let left = Arc::clone(&left);
        handles.push(thread::spawn(move || {
            let mut sold = 0;
            for _ in 0..want {
                // 보는 일과 빼는 일을 한 번 잠근 채로 한다.
                let mut tickets = left.lock().unwrap();
                if *tickets == 0 {
                    break;
                }
                *tickets -= 1;
                sold += 1;
            }
            sold
        }));
    }
    let mut total = 0;
    for handle in handles {
        total += handle.join().unwrap();
    }
    let remain = *left.lock().unwrap();
    (total, remain)
}

fn main() {
    for wants in [[50, 40, 30], [20, 30, 10], [0, 0, 100]] {
        let asked: u32 = wants.iter().sum();
        let (sold, left) = sell(100, &wants);
        print!("{asked:>3}장을 팔려 했다: ");
        println!("판 표 {sold:>3}장, 남은 표 {left:>2}장");
    }
}
