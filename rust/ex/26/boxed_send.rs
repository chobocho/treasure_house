use std::thread;

fn main() {
    let job: Box<dyn Fn() -> u32 + Send> = Box::new(|| 6 * 7);
    let h = thread::spawn(move || job());
    println!("{}", h.join().unwrap());
}
