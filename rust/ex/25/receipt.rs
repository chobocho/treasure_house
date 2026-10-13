fn main() {
    let pencil_qty = 3;
    let pencil_price = 450;
    let notebook_qty = 2;
    let notebook_price = 1200;
    let eraser_qty = 10;
    let eraser_price = 80;
    let pencil = pencil_qty * pencil_price;
    let notebook = notebook_qty * notebook_price;
    let eraser = eraser_qty * eraser_price;
    println!(
        "{:<3} {:<8} {:>3} {:>5} {:>6}",
        "NO", "ITEM", "QTY", "PRICE", "AMOUNT"
    );
    println!(
        "{:03} {:<8} {:>3} {:>5} {:>6}",
        1, "pencil", pencil_qty, pencil_price, pencil
    );
    println!(
        "{:03} {:<8} {:>3} {:>5} {:>6}",
        2, "notebook", notebook_qty, notebook_price, notebook
    );
    println!(
        "{:03} {:<8} {:>3} {:>5} {:>6}",
        3, "eraser", eraser_qty, eraser_price, eraser
    );
    println!("{:-<29}", "");
    println!("{:<22} {:>6}", "TOTAL", pencil + notebook + eraser);
}
