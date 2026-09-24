# Proposing Changes to Go

## Introduction

The Go project's development process is design-driven.
Significant changes to the language, libraries, or tools
(which includes API changes in the main repo and all golang.org/x repos,
as well as command-line changes to the `go` command)
must be first discussed, and sometimes formally documented,
before they can be implemented.

This document describes the process for proposing, documenting, and
implementing changes to the Go project.

To learn more about Go's origins and development process, see the talks
[How Go Was Made](https://go.dev/talks/2015/how-go-was-made.slide),
[The Evolution of Go](https://go.dev/talks/2015/gophercon-goevolution.slide),
and [Go, Open Source, Community](https://go.dev/blog/open-source)
from GopherCon 2015.

## The Proposal Process

The proposal process is the process for reviewing a proposal and reaching
a decision about whether to accept or decline the proposal.

1. The proposal author [creates a brief issue](https://go.dev/issue/new) describing the proposal.\
   Note: There is no need for a design document at this point.\
   Note: A non-proposal issue can be turned into a proposal by simply adding the proposal label.\
   Note: [Language changes](#language-changes) should follow a separate [template](go2-language-changes.md)

