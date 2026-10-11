fn main() {
    let csv = "kim,31,seoul";
    let fields: Vec<&str> = csv.split(',').collect();
    println!("{fields:?}");

    let words: Vec<&str> =
        "  여러   칸  공백 ".split_whitespace().collect();
    println!("{words:?}");

    for (n, line) in "첫 줄\n둘째 줄\n".lines().enumerate() {
        println!("{}: {line}", n + 1);
    }
    println!("{:?}", "key=value=more".split_once('='));
    println!("{:?}", "a,b,,c".split(',').collect::<Vec<_>>());
}
