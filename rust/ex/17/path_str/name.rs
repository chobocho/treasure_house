use std::env;
use std::path::PathBuf;

fn main() {
    // args_os 는 인자를 String 이 아니라 OsString 으로 준다
    for arg in env::args_os().skip(1) {
        let path = PathBuf::from(arg);
        println!("{{:?}}     {path:?}");
        println!("display  {}", path.display());
        println!("to_str   {:?}", path.to_str());
    }
}
