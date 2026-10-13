#[derive(Debug)]
enum Light {
    Green,
    Yellow,
    Red,
}

// 한 박자 뒤의 신호. pressed 는 건널목 단추가 눌려 있는가.
fn next(light: Light, pressed: bool) -> Light {
    match (light, pressed) {
        (Light::Green, false) => Light::Green,
        (Light::Green, true) => Light::Yellow,
        (Light::Yellow, _) => Light::Red,
        (Light::Red, true) => Light::Red,
    }
}

fn main() {
    let mut light = Light::Green;
    for pressed in [false, true, false, true, false, true] {
        light = next(light, pressed);
        println!("{pressed:<5} -> {light:?}");
    }
}
//@ expect: E0004
