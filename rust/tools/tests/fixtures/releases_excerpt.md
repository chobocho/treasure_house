Version 1.65.0 (2022-11-03)
==========================

Language
--------
- [Error on `as` casts of enums with `#[non_exhaustive]` variants](https://github.com/rust-lang/rust/pull/92744/)
- [Stabilize `let else`](https://github.com/rust-lang/rust/pull/93628/)
- [Stabilize generic associated types (GATs)](https://github.com/rust-lang/rust/pull/96709/)
- [Add lints `let_underscore_drop` and `let_underscore_lock` from Clippy](https://github.com/rust-lang/rust/pull/97739/)
- [Stabilize `break`ing from arbitrary labeled blocks ("label-break-value")](https://github.com/rust-lang/rust/pull/99332/)
- [Uninitialized integers, floats, and raw pointers are now considered immediate UB](https://github.com/rust-lang/rust/pull/98919/).
  Usage of `MaybeUninit` is the correct way to work with uninitialized memory.
- [Stabilize raw-dylib for Windows x86_64, aarch64, and thumbv7a](https://github.com/rust-lang/rust/pull/99916/)
- [Do not allow `Drop` impl on foreign ADTs](https://github.com/rust-lang/rust/pull/99576/)

Compiler
--------
- [Stabilize -Csplit-debuginfo on Linux](https://github.com/rust-lang/rust/pull/98051/)
- [Use niche-filling optimization even when multiple variants have data](https://github.com/rust-lang/rust/pull/94075/)
- [Associated type projections are now verified to be well-formed prior to resolving the underlying type](https://github.com/rust-lang/rust/pull/99217/#issuecomment-1209365630)
- [Stringify non-shorthand visibility correctly](https://github.com/rust-lang/rust/pull/100350/)
- [Normalize struct field types when unsizing](https://github.com/rust-lang/rust/pull/101831/)
- [Update to LLVM 15](https://github.com/rust-lang/rust/pull/99464/)
- [Fix aarch64 call abi to correctly zeroext when needed](https://github.com/rust-lang/rust/pull/97800/)
- [debuginfo: Generalize C++-like encoding for enums](https://github.com/rust-lang/rust/pull/98393/)
- [Add `special_module_name` lint](https://github.com/rust-lang/rust/pull/94467/)
- [Add support for generating unique profraw files by default when using `-C instrument-coverage`](https://github.com/rust-lang/rust/pull/100384/)
- [Allow dynamic linking for iOS/tvOS targets](https://github.com/rust-lang/rust/pull/100636/)

New targets:

- [Add armv4t-none-eabi as a tier 3 target](https://github.com/rust-lang/rust/pull/100244/)
- [Add powerpc64-unknown-openbsd and riscv64-unknown-openbsd as tier 3 targets](https://github.com/rust-lang/rust/pull/101025/)
  - Refer to Rust's [platform support page][platform-support-doc] for more
    information on Rust's tiered platform support.

Libraries
---------

- [Don't generate `PartialEq::ne` in derive(PartialEq)](https://github.com/rust-lang/rust/pull/98655/)
- [Windows RNG: Use `BCRYPT_RNG_ALG_HANDLE` by default](https://github.com/rust-lang/rust/pull/101325/)
- [Forbid mixing `System` with direct system allocator calls](https://github.com/rust-lang/rust/pull/101394/)
- [Document no support for writing to non-blocking stdio/stderr](https://github.com/rust-l

Version 1.62.1 (2022-07-19)
==========================

Rust 1.62.1 addresses a few recent regressions in the compiler and standard
library, and also mitigates a CPU vulnerability on Intel SGX.

* [The compiler fixed unsound function coercions involving `impl Trait` return types.][98608]
* [The compiler fixed an incremental compilation bug with `async fn` lifetimes.][98890]
* [Windows added a fallback for overlapped I/O in synchronous reads and writes.][98950]
* [The `x86_64-fortanix-unknown-sgx` target added a mitigation for the
  MMIO stale data vulnerability][98126], advisory [INTEL-SA-00615].

[98608]: https://github.com/rust-lang/rust/issues/98608
[98890]: https://github.com/rust-lang/rust/issues/98890
[98950]: https://github.com/rust-lang/rust/pull/98950
[98126]: https://github.com/rust-lang/rust/pull/98126
[INTEL-SA-00615]: https://www.intel.com/content/www/us/en/security-center/advisory/intel-sa-00615.html

Version 1.0.0 (2015-05-15)
========================

* ~1500 changes, numerous bugfixes

Highlights
----------

* The vast majority of the standard library is now `#[stable]`. It is
  no longer possible to use unstable features with a stable build of
  the compiler.
* Many popular crates on [crates.io] now work on the stable release
  channel.
* Arithmetic on basic integer types now [checks for overflow in debug
  builds][overflow].

Language
--------

* Several [restrictions have been added to trait coherence][coh] in
  order to make it easier for upstream authors to change traits
  without breaking downstream code.
* Digits of binary and octal literals are [lexed more eagerly][lex] to
  improve error messages and macro behavior. For example, `0b1234` is
  now lexed as `0b1234` instead of two tokens, `0b1` and `234`.
* Trait bounds [are always invariant][inv], eliminating the need for
  the `PhantomFn` and `MarkerTrait` lang items, which have been
  removed.
* ["-" is no longer a valid character in crate names][cr], the `extern crate
  "foo" as bar` syntax has been replaced with `extern crate foo as
  bar`, and Cargo now automatically translates "-" in *package* names
  to underscore for the crate name.
* [Lifetime shadowing is an error][lt].
* [`Send` no longer implies `'static`][send-rfc].
* [UFCS now supports trait-less associated paths][moar-ufcs] like
  `MyType::default()`.
* Primitive types [now have inherent methods][prim-inherent],
  obviating the need for extension 

Version 0.2  (2012-03-29)
=========================

   * >1500 changes, numerous bugfixes

   * New docs and doc tooling

   * New port: FreeBSD x86_64

   * Compilation model enhancements
      * Generics now specialized, multiply instantiated
      * Functions now inlined across separate crates

   * Scheduling, stack and threading fixes
      * Noticeably improved message-passing performance
      * Explicit schedulers
      * Callbacks from C
      * Helgrind clean

   * Experimental new language features
      * Operator overloading
      * Region pointers
      * Classes

   * Various language extensions
      * C-callback function types: 'crust fn ...'
      * Infinite-loop construct: 'loop { ... }'
      * Shorten 'mutable' to 'mut'
      * Required mutable-local qualifier: 'let m

Version 0.1  (2012-01-20)
===============================

   * Most language features work, including:
      * Unique pointers, unique closures, move semantics
      * Interface-constrained generics
      * Static interface dispatch
      * Stack growth
      * Multithread task scheduling
      * Typestate predicates
      * Failure unwinding, destructors
      * Pattern matching and destructuring assignment
      * Lightweight block-lambda syntax
      * Preliminary macro-by-example

   * Compiler works with the following configurations:
      * Linux: x86 and x86_64 hosts and targets
      
