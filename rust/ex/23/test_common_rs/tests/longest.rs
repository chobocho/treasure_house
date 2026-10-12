mod common;

#[test]
fn longest_is_three() {
    assert_eq!(wordbox::longest(&common::sample()), "three");
}
