fn main() {
    let lines = ["rust is fun", "so is go"];

    // map 으로 하면 반복자의 반복자가 된다. flat_map 은 한 겹으로 편다.
    let words: Vec<&str> =
        lines.iter().flat_map(|l| l.split(' ')).collect();
    println!("{words:?}");

    // 이미 겹쳐 있는 것은 flatten.
    let nested = vec![vec![1, 2], vec![], vec![3]];
    let flat: Vec<i32> = nested.into_iter().flatten().collect();
    println!("{flat:?}");
}
