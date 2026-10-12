# Outline — Rust 기초 문법집 (target 945 slides, hard cap 2000 since 2026-10-12)

Chapter-level contract for the whole book. A writer takes one part (or half) and must
stay inside its row: what is listed under another part is taught there, not here — link
to that part's cover (`#pNN`) instead of re-teaching. Slide counts include the part
cover, the intro slide, chapter covers and quizzes. Stay within ±10 % of the part total.

Reader: knows one other language (Python/JS/C/Java), new to Rust. Order of the book is the
reading order — do not use syntax before the part that introduces it unless you say
"N부에서 봅니다" in one clause (e.g. part 2 may print a `Vec` with `{:?}` but must not
explain vectors).

## 0부 읽는 법 — 이 책의 증거 방식 (15) — orchestrator
How to read a slide (code box, dark capture box, `$` line), the machine (rustc 1.99.0,
aarch64 Android, Termux), why `--edition 2024` is always shown, expected-failure examples,
the three normalizations, version badges and sources, map of the book.

## 1부 Rust의 역사 (60) — orchestrator
Origins (Graydon Hoare's side project → Mozilla sponsorship → first public release 0.1),
the pre-1.0 churn (what was removed: green threads, GC pointers, sigils), 1.0 and the
stability promise, release trains (6-week cycle, stable/beta/nightly), editions
2015/2018/2021/2024 and what each changed, milestones (NLL, async/await, const generics,
GATs, let-else, async fn in traits …), governance (Mozilla layoffs → Rust Foundation),
adoption (Firefox, Linux kernel, Android), timeline table, quiz.

## 2부 첫걸음 — 도구와 출력 (40)
1. 첫 프로그램 (done: hello, rustc, comments, semicolon error, `println` vs `println!`, editions)
2. cargo — `cargo new` layout, Cargo.toml, `cargo run/build/check`, debug vs `--release`,
   `rustfmt`, clippy (one real lint), where the binary lands
3. println! 서식 — `{}` vs `{:?}` vs `{:#?}`, positional/named/inline arguments, width, fill,
   alignment, precision, sign, bases (`{:x}` `{:b}` `{:#o}`), `{{ }}`, `print!` `eprintln!`
   `format!` `dbg!`, the "doesn't implement Display" error (E0277)
4. 입력 — `std::io::stdin().read_line`, `trim` + `parse`, `std::env::args`
   (no error-handling theory: `expect` only, point to 9부)

## 3부 변수와 기본 타입 (60)
1. 변수 — `let`, immutability by default (E0384), `mut`, shadowing vs mutation, scope and
   blocks, unused-variable warning and `_x`, `const` vs `static` (no `static mut`)
2. 정수 — i8…i128/u8…u128/isize/usize, literals (`1_000`, `0xff`, `0o17`, `0b1`, `b'a'`,
   suffixes), inference default i32, MIN/MAX, overflow: debug panic vs release wrap
   (`-O`), `checked_/wrapping_/saturating_/overflowing_`, division/remainder semantics
3. 실수·불·문자 — f32/f64, NaN and comparisons, `as` rounding, bool, `char` is a Unicode
   scalar (4 bytes), escapes
4. 형변환 — no implicit conversion (E0308), `as` and its truncation, `From/Into` for
   lossless (`i64::from(x)`), `TryFrom` for checked, `parse::<T>()`, type annotations and
   turbofish
5. 튜플·배열 — tuple indexing/destructuring, unit `()`, arrays `[T; N]`, `[0; 5]`,
   out-of-bounds panic, `len`, arrays vs slices (slices proper are in 6부)

## 4부 식과 제어 흐름 (50)
1. 식과 문 — everything-is-an-expression, block value, the trailing-semicolon mistake
   (E0308 `()`), `let` with block
2. if — condition must be bool (E0308), `if` as an expression, branch types must match,
   `else if` chains, no ternary
3. 반복 — `loop` + `break value`, `while`, `for` over ranges (`..`, `..=`, `rev`,
   `step_by`), `for` over arrays, loop labels (`'outer:`), `continue`
4. match 맛보기 — `match` on integers/chars, `_`, ranges and `|`, must be exhaustive
   (E0004), `match` as an expression (full pattern syntax is in 7부)

## 5부 함수 (35)
Definition, parameters need types, return type and the tail expression, `return` early,
unit-returning functions, expression-bodied helper style, nested functions, function
pointers `fn(i32) -> i32`, passing functions as arguments, recursion (factorial, fib),
diverging `!` (`panic!`, `loop`), `const fn` (one slide), doc comments `///` (one slide),
no overloading / no default arguments (show the idiom), shadowing parameters.
(Closures are 12부; generics 10부; ownership of parameters 6부.)

## 6부 소유권·빌림·슬라이스 (85)  — files 06_own.html (1–3), 06b_own.html (4–6)
1. 왜 소유권인가 — stack vs heap in one picture, `String` vs `&str` first contact, scope
   and `drop`, RAII
2. 이동 — move on assignment (E0382), move into a function, returning ownership, `clone`,
   `Copy` types (which types are Copy and why), partial move out of a tuple/struct
3. 참조와 빌림 — `&T`, `&mut T`, borrowing in function signatures, deref `*`, auto-deref on
   method calls
4. 빌림 규칙 — many readers XOR one writer (E0502, E0499), non-lexical lifetimes (borrow
   ends at last use), mutation through `&` forbidden (E0596), dangling reference rejected
   (E0106/E0515 — name lifetimes only, details in 11부), iterator invalidation example
5. 슬라이스 — `&[T]`, `&str` as a slice, ranges, `first_word` classic, slices keep the
   borrow alive (E0502), byte index vs char boundary panic, `&mut [T]`, `split_at_mut`
6. 실전 패턴 — take `&str`/`&[T]` not `&String`/`&Vec<T>`, return owned vs borrowed,
   `mem::swap`/`take`/`replace`, `Option::take`, clone-to-satisfy-the-checker smell

## 7부 구조체·열거형·패턴 매칭 (80) — files 07_data.html (1–3), 07b_data.html (4–6)
1. 구조체 — definition, instantiation, field init shorthand, update syntax `..`, tuple
   structs, unit structs, `#[derive(Debug)]`, whole struct must be `mut`
2. 메서드 — `impl`, `&self` / `&mut self` / `self`, associated functions (`new`), multiple
   `impl` blocks, method call auto-ref, `Self`
3. 열거형 — variants with data (unit/tuple/struct), `impl` on enums, C-like enums and `as`,
   `Option<T>` (no null), size of an enum
4. match 전부 — destructuring structs/tuples/enums/references, bindings `@`, guards `if`,
   `|`, ranges, `..` and `_`, ref/ref mut vs default binding modes, exhaustiveness
5. if let · let else · while let — `if let`, `else`, `let … else`, `while let` (stack pop),
   `matches!`, let-chains (`if let … && cond`) with its version badge
6. 패턴이 쓰이는 모든 자리 — `let`, function parameters, `for`, refutable vs irrefutable
   (E0005), nested enums, a small state-machine example

## 8부 문자열과 컬렉션 (70) — files 08_coll.html (1–2), 08b_coll.html (3–5)
1. String과 &str — UTF-8, creating, `push_str`/`push`/`+`/`format!`, no indexing (E0277),
   `len` is bytes, `chars()` vs `bytes()`, slicing at char boundaries, common methods
   (`trim`, `split`, `replace`, `contains`, `to_uppercase`, `lines`, `parse`), `&String`→`&str`
2. Vec — `Vec::new`/`vec!`, push/pop, index vs `get`, iterate `&v`/`&mut v`/`v`, capacity,
   `insert`/`remove`/`retain`/`sort`/`dedup`, borrow + push error (E0502), slices of a Vec
3. HashMap — insert/get, `entry().or_insert`, word count, iteration order is not stable
   (do NOT print raw iteration order — sort first), ownership of keys/values, `BTreeMap`
4. 그 밖의 컬렉션 — `HashSet`/`BTreeSet`, `VecDeque`, `BinaryHeap`, when to use which (table)
5. 문자열 실전 — `char` methods, byte strings, raw strings `r#""#`, `to_string` vs
   `String::from` vs `into`, `Cow` (one slide), string formatting recap

## 9부 오류 처리 (55)
1. panic — `panic!`, unwinding, exit code 101, `RUST_BACKTRACE` (mention), when panic is
   right (bugs, not expected failures)
2. Option — `Some/None`, `unwrap`/`expect`, `unwrap_or(_else/_default)`, `map`, `and_then`,
   `ok_or`, `?` on Option, `is_some_and`
3. Result — `Ok/Err`, `match`, `unwrap`/`expect`, `map_err`, `?` operator, `?` needs a
   compatible return type (E0277), `main` returning `Result`, exit code 1
4. 내 오류 타입 — enum error, `impl Display`, `impl std::error::Error`, `From` for `?`
   conversion, `Box<dyn Error>`, `source()`
5. 실전 — parse a config line by line with line numbers, collecting
   `Result<Vec<_>, _>`, `Option` ↔ `Result`, when to panic vs return

## 10부 제네릭과 트레이트 (80) — files 10_trait.html (1–3), 10b_trait.html (4–6)
1. 제네릭 — generic functions, structs, enums, `impl<T>`, monomorphization (zero cost),
   missing bound error (E0369/E0277)
2. 트레이트 — define, implement, default methods, trait as parameter (`impl Trait`), trait
   bounds, `where`, multiple bounds `+`, returning `impl Trait`, orphan rule (E0117)
3. 표준 트레이트 ① — `Debug`, `Display`, `Clone`, `Copy`, `PartialEq/Eq`,
   `PartialOrd/Ord`, `Hash`, `Default`; what `#[derive]` generates
4. 표준 트레이트 ② — `From/Into`, `TryFrom`, `AsRef`, `FromStr`, `Iterator` (preview),
   `Drop`, operator overloading (`Add`, `Neg`, `Index`, `AddAssign`)
5. 트레이트 객체 — `dyn Trait`, `Box<dyn Trait>`, `&dyn Trait`, static vs dynamic dispatch,
   heterogeneous `Vec`, dyn compatibility (object safety) error (E0038)
6. 더 깊이 — associated types, associated consts, generic vs associated type, supertraits,
   blanket impls, const generics `[T; N]`, extension-trait pattern

## 11부 수명 (45)
Why lifetimes exist (dangling), the `longest` classic (E0106), annotation syntax `'a`,
what the annotation promises, elision rules (three rules, with examples that need none),
lifetimes in structs (E0597 when the owner dies first), `impl<'a>`, `'static`, lifetime
bounds `T: 'a`, common errors and fixes (return owned instead, restructure scopes),
`'_`, a reading drill (5 signatures), quiz.

## 12부 클로저와 반복자 (60) — files 12_iter.html (1–2), 12b_iter.html (3–5)
1. 클로저 — syntax, type inference, capturing by ref / mut ref / move, `Fn`/`FnMut`/`FnOnce`,
   closures as parameters and return values, `move` closures
2. Iterator 트레이트 — `next`, `iter`/`iter_mut`/`into_iter`, laziness (nothing happens until
   consumed — show the unused warning), implementing `Iterator` for a struct
3. 어댑터 — `map`, `filter`, `enumerate`, `zip`, `skip`/`take`, `chain`, `rev`, `flat_map`,
   `filter_map`, `take_while`/`skip_while`, `peekable`, `windows`/`chunks`
4. 소비자 — `collect` (Vec/String/HashMap/Result), `sum`/`product`, `count`, `fold`,
   `min`/`max(_by_key)`, `any`/`all`, `find`/`position`, `for_each`
5. 실전 — loop → iterator rewrite, sort_by / sort_by_key / sort_unstable, grouping with
   HashMap, `iter::from_fn`/`successors`/`repeat`, performance note (zero-cost)

## 13부 모듈·크레이트·시험·문서 (50)
1. 모듈 — `mod`, `pub`, paths (`crate::`, `self::`, `super::`), `use`, `as`, nested and
   glob imports, re-export `pub use`, privacy of struct fields (E0616/E0603)
2. 파일로 나누기 — `mod foo;` → `foo.rs` / `foo/mod.rs`, a 3-file cargo project
   (directory example), binary vs library crate (`main.rs` + `lib.rs`)
3. cargo 더 — Cargo.toml sections, profiles, features (concept), workspaces (concept),
   crates.io and semver (explain only — this book uses no external crates)
4. 시험 — `#[test]`, `assert!`/`assert_eq!`/`assert_ne!`, `#[should_panic]`,
   `Result`-returning tests, `#[cfg(test)] mod tests`, integration tests in `tests/`,
   `cargo test` output
5. 문서 — `///`, `//!`, doc tests (they run!), `cargo doc` (mention), attributes recap
   (`#[allow]`, `#[derive]`, `#[cfg]`, `#[must_use]`)

## 14부 스마트 포인터 (45)
`Box<T>` (heap, recursive types — E0072 then fix), `Deref` and deref coercion, `Drop`
order, `Rc<T>` (shared ownership, `strong_count`), `RefCell<T>` (interior mutability,
runtime borrow panic), `Rc<RefCell<T>>`, `Weak<T>` and reference cycles (tree with parent
links), `Cell<T>`, `Box<dyn Trait>` recap, choosing table (Box/Rc/Arc/RefCell/Mutex).

## 15부 동시성 기초 (40)
`thread::spawn` + `join`, `move` closures (E0373), scoped threads (`thread::scope`),
channels (`mpsc`), `Mutex<T>` and its guard, `Arc<Mutex<T>>`, `Rc` is not `Send` (E0277),
`Send`/`Sync` in one slide each, atomics, `RwLock`, deadlock (explain, do not run),
`OnceLock`/`LazyLock`. **Every capture must be deterministic** — join in a fixed order,
sort results, never print from racing threads.

## 16부 매크로·unsafe·async 맛보기 (40)
1. 매크로 — `macro_rules!` (one-arm, repetition `$(...),*`, a `hashmap!`), hygiene in one
   example, derive/attribute macros are "procedural" (explain only), useful std macros
   (`vec!`, `assert!`, `todo!`, `unreachable!`, `concat!`, `stringify!`, `line!`, `cfg!`)
2. unsafe — the five superpowers, raw pointers, `unsafe fn`, safe wrapper around unsafe,
   `extern "C"` call into libc (`abs`/`strlen`), what unsafe does NOT turn off
3. async 맛보기 — `async fn` returns a Future, futures are lazy, a ~25-line `block_on` on
   std (`Waker::noop` / `pin!`), why real programs use a runtime crate (explain only)
4. 그 밖의 문법 — type aliases, `impl Trait` in more places, never type, labeled blocks,
   `const` blocks/items, shadowed prelude, raw identifiers `r#`

## 부록 (35) — orchestrator
Keyword table (strict/reserved/weak), operator table with precedence, format-spec cheat
sheet, error-code index (every E-code shown in the book → slide link), edition
differences table, glossary (Korean ↔ English), sources.
