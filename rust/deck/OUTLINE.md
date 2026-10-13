# Outline — Rust 기초 문법집 (target ≈1,870 slides, hard cap 2000 since 2026-10-12)

> Parts 0–16 are the first edition (922 slides, reviewed twice). Parts 17–26 and the
> additions listed under "Expansion" at the end were approved on 2026-10-12. The appendix
> moved from part 17 to part 27 (ids `p27-*`, examples `ex/27`).

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

## 부록 = part 27 (45) — orchestrator
Keyword table (strict/reserved/weak), operator table with precedence, format-spec cheat
sheet, error-code index (every E-code shown in the book → slide link), edition
differences table, glossary (Korean ↔ English), sources.

---

# Expansion (approved 2026-10-12) — parts 17–26

Same rules as the first edition: std only, every example really compiled and run by
`tools/rsrun.py`, compile-error examples allowed with their fixed twin, captures must be
deterministic. Three bands: 17–23 "표준 라이브러리와 심화", 24–26 "실전", 27 부록.
Writers follow `AUTHORING.md` AND the style sheet in `REVIEW2.md` from the start
(fixed terms, slide-level links, "acknowledge the earlier slide in one clause").

## 17부 입출력과 파일 (90) — files 17_io.html (1–3), 17b_io.html (4–6)
1. 표준 출력과 오류 출력 — `print!` vs `println!` vs `eprintln!` (stdout/stderr shown apart
   with a RUN-file redirect), `io::stdout().lock()`, `write!`/`writeln!` on `io::Write`
   (cash in p09-err-display's `write!`), `flush`, `process::exit` vs returning `ExitCode`
2. 표준 입력 — `read_line` recap (p02-parse-trim), `stdin().lines()`, `BufRead`, a number
   per line with `?`, end of input, summing a column (`//@ stdin:` directive)
3. 파일 읽기 — `fs::read_to_string`, `File::open` + `BufReader::lines`, missing file →
   `io::Error` and `ErrorKind::NotFound`, `io::Result`, bytes with `fs::read`
4. 파일 쓰기 — `fs::write`, `File::create`, `OpenOptions` (append), `BufWriter`, formatted
   lines, what happens to buffered data on drop
5. 경로와 디렉터리 — `Path`/`PathBuf`, `join`, `file_name`/`extension`/`parent`,
   `exists`, `create_dir_all`, `read_dir` (SORT before printing), `metadata().len()`,
   `remove_file`/`remove_dir_all`, why paths are not `String` (`OsStr`, `display()`)
6. 작은 도구 — `cat`, `wc`, `head` in miniature: args + files + stdin fallback + errors
   with the file name; functions generic over `R: BufRead` / `W: Write` tested with
   `&[u8]` / `Vec<u8>` / `io::Cursor`; `From<io::Error>` for an own error (p09-err-from)

## 18부 표준 라이브러리 둘러보기 (80) — files 18_std.html (1–3), 18b_std.html (4–6)
1. 수 더 깊이 — bit operators and shifts, `count_ones`/`leading_zeros`/`trailing_zeros`,
   `pow`, `rem_euclid`, `abs_diff`, `i128`, `from_str_radix`, `to_be_bytes`/`from_le_bytes`,
   float `to_bits`, `checked_*`/`wrapping_*`/`saturating_*` only as a link to p03
2. 비교와 정렬 — `Ordering`, `cmp`/`partial_cmp`/`total_cmp`, `then_with`, `Reverse`,
   `min`/`max`/`clamp`, sorting by several keys, `sort` vs `sort_unstable` (show what
   stability means on equal keys), `binary_search`, `partition_point`
3. 해시와 맵 더 — implementing `Hash` by hand, the `Eq`/`Hash` agreement, own key type,
   `BTreeMap::range`, `entry` API in full, `retain`, sets operations; never print a
   `HashMap` in iteration order
4. 시간 — `Duration` arithmetic and formatting (deterministic), `Instant` (compare, never
   print elapsed), `SystemTime`/`UNIX_EPOCH` (explain; print nothing that varies)
5. 프로세스와 환경 — `env::var`/`vars` (print only what the example sets), `Command`
   running a fixed program (`echo`, the example itself), exit status, piping output
6. 그 밖의 도구 — `mem::size_of`/`align_of`, `type_name`, `Option`/`Result` combinators
   not yet shown (`zip`, `xor`, `transpose`, `flatten`, `take`, `replace`, `get_or_insert`),
   iterator extras (`scan`, `last`, `nth`, `cycle().take`, `sum` of `Result`s), `char`
   and `str` extras (`split_whitespace`, `rsplit`, `strip_prefix`, `char::from_digit`)

## 19부 제네릭·트레이트 심화 (90) — files 19_gen.html (1–3), 19b_gen.html (4–6)
1. 바운드 더 깊이 — conditional `impl<T: Bound>` blocks, `where` on methods, `?Sized`,
   overlapping impls rejected (E0119), blanket impls revisited
2. 연관 타입과 GATs — a trait with an associated type by hand, associated consts in
   generic code, generic associated types (a lending iterator; version badge; cash in
   p01-let-else's GATs sentence)
3. 트레이트 객체 심화 — `dyn Any` and `downcast_ref`, designing a dyn-compatible trait
   (generic method → E0038 → `where Self: Sized`), `&dyn` vs `Box<dyn>` vs generics on one
   example, trait upcasting (version badge)
4. 타입으로 설계하기 — newtypes for units (metres vs feet: mixing is a compile error),
   `PhantomData`, the typestate pattern (calling `send` before `connect` does not
   compile), sealed traits, marker traits
5. 고차 바운드와 함수 — `for<'a>` bounds, closures that return references, `fn` pointer vs
   `impl Fn` vs `dyn Fn` as one table with evidence (sizes)
6. const 와 제네릭 — `const fn` (and what it cannot do: an E-code), const generics in
   depth (`impl<const N: usize>`, array of any length), consts computed at compile time
   (overflow in a const is a compile error)

## 20부 동시성 심화 (70) — file 20_conc.html (5 chapters)
1. 채널 더 — `sync_channel` (bounded, 0 = rendezvous), `try_recv`, `recv_timeout`
   (designed so the outcome is fixed), a three-stage pipeline
2. 기다리기와 깨우기 — `Condvar` with a `while` loop, `Barrier`, a blocking queue by hand
3. 공유 상태 설계 — mutex poisoning (a thread panics holding the lock → `PoisonError`),
   `try_lock`, lock ordering (explain; show the safe order), atomics and
   `compare_exchange`, `Ordering` (explain only)
4. 스레드 풀 만들기 — a worker pool step by step (channel + `Arc<Mutex<Receiver>>`),
   shutdown in `Drop`, results collected in a fixed order
5. thread_local 과 나눠 풀기 — `thread_local!`, scoped threads splitting a slice
   (`chunks`, parallel sum equals sequential sum), `available_parallelism` (do not print)
**Every capture deterministic** — join in a fixed order, sort results, never print from
racing threads, no timing numbers.

## 21부 매크로·unsafe·FFI 심화 (80) — files 21_low.html (1–2), 21b_low.html (3–4)
1. macro_rules! 심화 — all fragment specifiers that matter (`tt`, `pat`, `literal`,
   `block`, `item`), nested repetition, recursion and the tt-muncher, internal rules,
   optional trailing comma, `$crate` and `#[macro_export]` (directory example), reading a
   macro error, hygiene again
2. 날 포인터와 메모리 — `add`/`offset`, `read`/`write`, `NonNull`, `std::alloc` with
   `Layout`, `MaybeUninit`, `slice::from_raw_parts`, `transmute` vs `to_bits`/`from_bits`
3. 작은 Vec 만들기 — `MyVec<T>` step by step: allocate, `push`, grow, `Index`, `Drop`,
   `IntoIterator`; tested against `Vec`; say plainly that no UB checker (Miri) is
   available on this machine
4. FFI — more libc calls (`strlen`, `getenv`, `qsort` with a Rust callback), `CStr`/
   `CString`, `#[repr(C)]` structs, exporting with `#[unsafe(no_mangle)] extern "C"`
   (edition 2024 spelling — cash in p01-ed2024), `union` (brief), `static mut` and why
   the 2024 edition rejects references to it

## 22부 async 심화 (60) — files 22_async.html (1–3), 22b_async.html (4–5)
1. Future 를 손으로 — `impl Future` by hand (a countdown that returns `Pending` n times),
   `Poll`, `Context`, what a `Waker` is for (a counting waker built with the `Wake` trait)
2. 실행기 키우기 — from part 16's `block_on` to a queue of tasks: `spawn`, run until all
   done, fixed order; joining two futures by hand; a hand-made `yield_now`
3. Pin — why (a value that points into itself must not move), `Pin<&mut T>`, `pin!`,
   `Box::pin`, `Unpin`
4. async 문법 더 — async blocks capturing, async closures (version badge), `async fn` in
   traits (cash in p01-afit; version badge), cancelling = dropping (a `Drop` print as
   evidence), a future that is not `Send` (the error)
5. 타이머 없이 — a channel and a "sleep" counted in ticks on the toy executor; what a
   real runtime adds (explain only, no external crates)

## 23부 Cargo·프로젝트 심화 (60) — files 23_cargo.html (1–3), 23b_cargo.html (4–5); directory examples
1. 워크스페이스 — two crates (lib + bin) with a path dependency, `cargo run -p`, one
   `Cargo.lock`/`target`
2. features — real flags: `[features]`, `#[cfg(feature = "…")]`, default features,
   `--features` / `--no-default-features` changing the output
3. build.rs 와 컴파일 때 정보 — a build script emitting `cargo::rustc-cfg`, `env!`
   (`CARGO_PKG_VERSION`), `option_env!`, `include_str!`
4. 시험 더 — helpers shared between tests, `should_panic(expected = …)`, testing a
   binary through its lib, a golden-file test, `--test-threads=1` and why this book pins it
5. 실행 파일 여러 개와 프로필 — `src/bin/*`, `examples/`, profile settings whose effect a
   capture can show (`overflow-checks`, `debug-assertions`), the `[lints]` table
All offline; no external crates.

## 24부 실전 프로젝트 (160) — files 24_proj.html, 24b_proj.html, 24c_proj.html, 24d_proj.html
Four programs built in steps; every step compiles and runs; each ends with tests.
1. (24) 낱말 세기 `wc` — args, files and stdin, counts of lines/words/bytes/chars, errors
   with file names, lib + bin split, tests on `&[u8]`
2. (24b) 미니 `grep` — search, `-i` `-n` `-v` `-c` flags parsed by hand into a struct,
   several files, exit codes 0/1/2, tests
3. (24c) 식 계산기 — tokenizer → recursive-descent parser → evaluator; `enum Expr` with
   `Box`; own error type with positions; a REPL over stdin lines; tests
4. (24d) 작은 키-값 저장소 — commands `set`/`get`/`del`/`list`; a text file format;
   `trait Storage` with in-memory and file-backed impls; a scripted run with worker
   threads behind `Arc<Mutex<_>>`; tests
Each project opens with what it reuses (links to the teaching slides) and closes with
"더 해 볼 것". ~40 slides per project.

## 25부 연습 문제와 풀이 (120) — files 25_ex.html, 25b_ex.html
About 55 problems following parts 2–23 in order. One slide states the task and shows the
expected output; the next shows a solution that was run (RUN). Problems never need
anything the named part has not taught. Chapter per band: 2–5, 6–7, 8–9, 10–12, 13–16,
17–23.

## 26부 컴파일 오류 처방전 (70) — files 26_errs.html (1–3), 26b_errs.html (4–7)
By symptom, not by number: 소유권·빌림 / 타입 / 이름·모듈 / 수명 / 트레이트 / 패턴 / 그 밖.
Each entry is a pair — the smallest program that produces the error (real message) and
the fixed program. Prefer error codes NOT yet in the book (about 30 new codes), and for
codes already taught give a different situation plus a link to the teaching slide. The
appendix error index picks the codes up from the titles.

## 27 부록 (45) — orchestrator
First-edition tables plus: index rows for parts 17–26, the glossary terms that did not
fit (컬렉션, 교착, 누수, 터보피시 …) and terms the new parts define, an edition table.

## Additions to parts 0–16 (≈ +30; the rest of the head-room is in the budgets)
- 1부: quizzes for chapters 1, 2, 3, 5 (+4).
- 7부: a fixed twin for p07-enum-missing-arm (+1).
- 8부: borrow + push in a `Vec` (E0502, acknowledging p06-push-holding) (+1); a
  formatting recap that only links back to part 2 (+1).
- 9부: evidence for "Error 는 Debug 도 요구한다" (E0277) and for `unimplemented!` /
  `unreachable!` (+2).
- 10부: evidence that monomorphization makes one copy per type if a deterministic
  capture exists (e.g. distinct `fn` item addresses compared, not printed) — otherwise
  leave the sentence; what `#[derive]` generates (hand-written equivalent side by side) (+2).
- 11부: `T: 'a` bound (+2); a fixed twin for p11-static-required (+1).
- 12부: `sort` vs `sort_unstable` evidence moves to 18부 ch 2 — link only.
- 14부: `RefCell` guard lives until dropped (an unused guard still blocks) (+1); `Cell`
  needs `Copy` for `get` (E0599/E0277) (+1).
- 15부: `Mutex::lock` waits (a deterministic design) (+1); `move` with a `Copy` value (+1).
- 16부: never type `!` in more places, `impl Trait` in argument/return recap, shadowing
  a prelude name (+4); the closing note moves to its own slide and now hands over to
  part 17 instead of the appendix (+1).
