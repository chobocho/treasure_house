use std::marker::PhantomData;

// 택배의 세 상태 — 싼 것, 요금을 낸 것, 보낸 것.
struct Packed;
struct Paid;
struct Sent;

// 물건의 이름, 낸 요금, 그리고 상태의 표시.
struct Parcel<State>(&'static str, u32, PhantomData<State>);

impl Parcel<Packed> {
    fn pack(item: &'static str) -> Parcel<Packed> {
        Parcel(item, 0, PhantomData)
    }
}

impl Parcel<Paid> {
    fn send(self) -> Parcel<Sent> {
        Parcel(self.0, self.1, PhantomData)
    }
}

impl Parcel<Sent> {
    fn label(&self) -> String {
        format!("{} — 요금 {}원, 보냄", self.0, self.1)
    }
}

fn main() {
    let parcel = Parcel::pack("책 두 권");
    let parcel = parcel.pay(3500).send();
    println!("{}", parcel.label());
}
//@ expect: E0599
