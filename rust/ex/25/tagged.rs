// 열거형 하나와, 변형마다 붙인 글을 주고받는 구현을 함께 만든다.
macro_rules! tagged {
    ($name:ident { $($variant:ident = $tag:literal),+ $(,)? }) => {
        #[derive(Debug, Clone, Copy)]
        enum $name {
            $($variant),+
        }

        impl $name {
            // 변형 전부 — 적은 차례대로.
            const ALL: &'static [$name] = &[$($name::$variant),+];

            fn tag(self) -> &'static str {
                match self {
                    $($name::$variant => $tag),+
                }
            }

            fn from_tag(text: &str) -> Option<$name> {
                $(
                    if text == $tag {
                        return Some($name::$variant);
                    }
                )+
                None
            }
        }
    };
}

tagged! {
    Light { Red = "빨강", Yellow = "노랑", Green = "초록", }
}

tagged!(Coin { Head = "앞", Tail = "뒤" });

fn main() {
    for light in Light::ALL {
        println!("{light:?} = {}", light.tag());
    }
    println!("{:?}", Light::from_tag("노랑"));
    println!("{:?}", Light::from_tag("파랑"));
    println!("{}가지와 {}가지", Light::ALL.len(), Coin::ALL.len());
    println!("{:?} {}", Coin::from_tag("뒤"), Coin::Head.tag());
}
