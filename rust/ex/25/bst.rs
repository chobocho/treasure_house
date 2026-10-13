// 왼쪽에는 더 작은 수, 오른쪽에는 더 큰 수가 달린 나무.
enum Tree {
    Leaf,
    Node(Box<Tree>, u32, Box<Tree>),
}

impl Tree {
    // 없는 수면 잎 자리에 마디를 단다. 있는 수면 아무 일도 없다.
    fn insert(&mut self, new: u32) {
        match self {
            Tree::Leaf => {
                let leaf = Box::new(Tree::Leaf);
                *self = Tree::Node(leaf, new, Box::new(Tree::Leaf));
            }
            Tree::Node(left, value, right) => {
                if new < *value {
                    left.insert(new);
                } else if new > *value {
                    right.insert(new);
                }
            }
        }
    }

    // 왼쪽, 자기, 오른쪽 차례로 out 에 넣는다.
    fn in_order(&self, out: &mut Vec<u32>) {
        if let Tree::Node(left, value, right) = self {
            left.in_order(out);
            out.push(*value);
            right.in_order(out);
        }
    }

    // 뿌리에서 가장 먼 마디까지의 마디 수. 빈 나무는 0.
    fn depth(&self) -> u32 {
        match self {
            Tree::Leaf => 0,
            Tree::Node(left, _, right) => {
                1 + left.depth().max(right.depth())
            }
        }
    }
}

fn main() {
    let mut tree = Tree::Leaf;
    println!("깊이 {}", tree.depth());
    for n in [50, 30, 70, 20, 40, 30, 35] {
        tree.insert(n);
    }
    let mut sorted = Vec::new();
    tree.in_order(&mut sorted);
    println!("{sorted:?}");
    println!("깊이 {}", tree.depth());
}
