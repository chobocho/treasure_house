//! 테트리스 규칙 — 화면·키보드·시계를 전혀 모르는 순수 로직.
//!
//! TUI·GUI·WASM 세 판이 이 크레이트 하나를 같이 쓴다. 입출력이 없으니
//! `cargo test` 만으로 규칙 전체를 검증할 수 있다.

pub mod bag;
pub mod board;
pub mod game;
pub mod piece;

pub use bag::{Bag, Rng};
pub use board::{Board, HEIGHT, WIDTH};
pub use game::{Action, Game};
pub use piece::{Kind, Piece, Rot};
