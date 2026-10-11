// 필드가 없는 구조체 — 값보다 "타입" 이 필요할 때.
struct Marker;

fn main() {
    let _m = Marker;
    println!("{}", std::mem::size_of::<Marker>());
}
