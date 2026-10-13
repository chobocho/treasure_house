struct Job {
    name: String,
}

impl Drop for Job {
    fn drop(&mut self) {
        println!("{} 정리", self.name);
    }
}

fn main() {
    let job = Job {
        name: String::from("백업"),
    };
    let name = &job.name;
    println!("{name} 시작");
}
