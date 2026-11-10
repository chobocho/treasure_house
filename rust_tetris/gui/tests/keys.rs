// GUI 키 배치 시험 — "눌렸나?"를 묻는 함수를 가짜로 넘긴다.
use minifb::{Key, KeyRepeat};
use tetris_core::Action;
use tetris_gui::{BINDINGS, actions};

#[test]
fn nothing_pressed_nothing_happens() {
    assert!(actions(|_, _| false).is_empty());
}

#[test]
fn moves_repeat_but_rotation_does_not() {
    let rep = |k: Key| {
        BINDINGS.iter().find(|b| b.0 == k).map(|b| b.1).unwrap()
    };
    for k in [Key::Left, Key::Right, Key::Down] {
        assert!(
            matches!(rep(k), KeyRepeat::Yes),
            "{k:?} 는 누르고 있으면 반복"
        );
    }
    for k in [Key::Up, Key::X, Key::Z, Key::Space, Key::C, Key::P] {
        assert!(matches!(rep(k), KeyRepeat::No), "{k:?} 는 한 번만");
    }
}

#[test]
fn each_key_maps_to_its_action() {
    let cases = [
        (Key::Left, Action::Left),
        (Key::Right, Action::Right),
        (Key::Down, Action::SoftDrop),
        (Key::Up, Action::RotateCw),
        (Key::X, Action::RotateCw),
        (Key::Z, Action::RotateCcw),
        (Key::Space, Action::HardDrop),
        (Key::C, Action::Hold),
        (Key::P, Action::Pause),
        (Key::Escape, Action::Pause),
    ];
    for (key, want) in cases {
        assert_eq!(actions(|k, _| k == key), vec![want], "{key:?}");
    }
}

#[test]
fn several_keys_in_one_frame_keep_table_order() {
    let got = actions(|k, _| k == Key::Space || k == Key::Left);
    assert_eq!(got, vec![Action::Left, Action::HardDrop]);
}

#[test]
fn unbound_keys_are_ignored() {
    assert!(actions(|k, _| k == Key::F5 || k == Key::A).is_empty());
}
