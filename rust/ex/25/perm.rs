// "rwxr-x---" 같은 아홉 글자를 9비트 수로 바꾼다.
// '-' 가 아닌 자리의 비트를 켠다. 맨 왼쪽 글자가 가장 높은 비트다.
fn to_mode(text: &str) -> u32 {
    let mut mode = 0;
    for c in text.chars() {
        let bit = if c == '-' { 0 } else { 1 };
        mode = (mode << 1) | bit;
    }
    mode
}

// 9비트 수를 아홉 글자로 바꾼다.
fn to_text(mode: u32) -> String {
    let mut text = String::new();
    for i in (0..9).rev() {
        let letter = ['x', 'w', 'r'][i % 3];
        if mode & (1 << i) != 0 {
            text.push(letter);
        } else {
            text.push('-');
        }
    }
    text
}

fn main() {
    for text in ["rwxr-x---", "rw-r--r--", "---------"] {
        let mode = to_mode(text);
        println!("{text} = {mode:03o} = {mode:09b}");
    }
    for digits in ["750", "644", "007"] {
        let mode = u32::from_str_radix(digits, 8).unwrap();
        let group = (mode >> 3) & 0b111;
        println!("{digits} = {}  그룹 {group}", to_text(mode));
    }
}
