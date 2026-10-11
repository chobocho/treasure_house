fn main() {
    let mut names = vec![String::from("kim"), String::from("lee")];

    for n in names.iter() {
        print!("{} ", n.len()); // n: &String — 빌려서 읽는다
    }
    for n in names.iter_mut() {
        n.push('!'); // n: &mut String — 빌려서 고친다
    }
    println!("{names:?}");
    for n in names.into_iter() {
        print!("{n} "); // n: String — 가져간다. names 는 여기서 끝.
    }
    println!();
}
