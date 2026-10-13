// 빈칸으로 나뉜 낱말이 몇 개인지 센다
fn count_words(text: &str) -> usize {
    let bytes = text.as_bytes();
    let mut count = 0;
    let mut in_word = false;
    for i in 0..bytes.len() {
        if bytes[i] == b' ' {
            in_word = false;
        } else if !in_word {
            in_word = true;
            count += 1;
        }
    }
    count
}

fn main() {
    let title = String::from(" the  rust book ");
    let n = count_words(&title);
    println!("[{title}] 낱말 {n}개");
}
