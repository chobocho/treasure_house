use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    // 여럿이 함께 갖고(Rc), 그 가운데 누구든 고친다(RefCell).
    let score = Rc::new(RefCell::new(0));
    let player1 = Rc::clone(&score);
    let player2 = Rc::clone(&score);

    *player1.borrow_mut() += 10;
    *player2.borrow_mut() += 5;

    println!("{}", score.borrow());
    println!("주인 {}명", Rc::strong_count(&score));
}
