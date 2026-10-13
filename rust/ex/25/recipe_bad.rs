// "설탕 120" 같은 줄에서 무게(g)를 읽는다
fn grams(line: &str) -> Result<u32, String> {
    let (name, amount) =
        line.split_once(' ').ok_or(format!("{line}: 빈칸이 없다"))?;
    let g = amount.parse::<u32>()?;
    if g == 0 {
        return Err(format!("{name}: 0 은 적지 않는다"));
    }
    Ok(g)
}

// 재료의 무게를 모두 더한다. 읽지 못한 줄이 있으면 거기서 그만둔다.
fn total(recipe: &[&str]) -> Result<u32, String> {
    let mut sum = 0;
    for line in recipe {
        sum += grams(line)?;
    }
    Ok(sum)
}

fn main() -> Result<(), String> {
    println!("{}g", total(&["밀가루 500", "설탕 120", "소금 8"])?);
    println!("{:?}", total(&["밀가루", "설탕 120"]));
    println!("{:?}", total(&["밀가루 500", "물 0"]));
    println!("{}g", total(&["밀가루 500", "설탕 한줌"])?);
    Ok(())
}
//@ expect: E0277
