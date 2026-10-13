// 글을 빌려 들고, 낱말을 앞에서부터 하나씩 내준다.
struct Words<'a> {
    rest: &'a str,
}

impl<'a> Words<'a> {
    fn new(text: &'a str) -> Self {
        Words { rest: text }
    }

    // 내준 낱말은 self 가 아니라 원래 글에 묶인다.
    fn next_word(&mut self) -> Option<&'a str> {
        let text = self.rest.trim();
        let (word, rest) = text.split_once(' ').unwrap_or((text, ""));
        self.rest = rest;
        if word == "" { None } else { Some(word) }
    }
}

fn main() {
    let text = String::from("  느린 것이   빠른 것이다 ");
    let mut found = Vec::new();
    {
        let mut words = Words::new(&text);
        while let Some(word) = words.next_word() {
            println!("[{word}] 남은 글 [{}]", words.rest);
            found.push(word);
        }
        println!("{:?}", words.next_word());
    } // words 는 여기서 사라진다
    println!("{found:?}");
    println!("{:?}", Words::new("   ").next_word());
}
