use std::borrow::Cow;

// 고칠 것이 없으면 빌린 채로, 있으면 새로 만들어 돌려준다.
fn no_spaces(s: &str) -> Cow<'_, str> {
    if s.contains(' ') {
        Cow::Owned(s.replace(' ', "_"))
    } else {
        Cow::Borrowed(s)
    }
}

fn main() {
    for input in ["hello", "hello big world"] {
        let out = no_spaces(input);
        let kind = match &out {
            Cow::Borrowed(_) => "빌림",
            Cow::Owned(_) => "새로 만듦",
        };
        println!("{out} ({kind})");
    }
}
