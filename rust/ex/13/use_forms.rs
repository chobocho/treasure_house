// 한 줄에 여럿, 별명(as), 전부(*).
use std::collections::{BTreeMap, BTreeSet};
use std::f64::consts::*;
use std::fmt::Result as FmtResult;
use std::io::Result as IoResult;

fn show() -> FmtResult {
    Ok(())
}

fn load() -> IoResult<u32> {
    Ok(7)
}

fn main() {
    let mut m = BTreeMap::new();
    m.insert("pi", PI); // consts::* 로 들어온 이름
    let s: BTreeSet<u32> = [3, 1, 2].into_iter().collect();
    println!("{m:?} {s:?} {:?} {:?}", show(), load().ok());
}
