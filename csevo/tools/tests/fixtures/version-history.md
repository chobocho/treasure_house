---
title: The history of C#
description: Learn how the C# language has changed over its many releases. Learn when different features were introduced in the language.
author: erikdietrich
ms.date: 11/18/2025
ms.custom: "updateeachrelease"
---

# The history of C\#

This article provides a history of each major release of the C# language. The C# team is continuing to innovate and add new features. Detailed language feature status, including features considered for upcoming releases can be found [on the dotnet/roslyn repository](https://github.com/dotnet/roslyn/blob/main/docs/Language%20Feature%20Status.md) on GitHub. To find when a particular feature was added to the language, consult the [C# version history](https://github.com/dotnet/csharplang/blob/main/Language-Version-History.md) file in the [`dotnet/csharplang`](https://github.com/dotnet/csharplang) repository on GitHub.

> [!IMPORTANT]
> The C# language relies on types and methods in what the C# specification defines as a *standard library* for some of the features. The .NET platform delivers those types and methods in a number of packages. One example is exception processing. Every `throw` statement or expression is checked to ensure the object being thrown is derived from <xref:System.Exception>. Similarly, every `catch` is checked to ensure that the type being caught is derived from <xref:System.Exception>. Each version may add new requirements. To use the latest language features in older environments, you may need to install specific libraries. These dependencies are documented in the page for each specific version. You can learn more about the [relationships between language and library](relationships-between-language-and-library.md) for background on this dependency.

## C# version 14

*Released November 2025*

C# 14 includes the following new features:

- [Extension members](./csharp-14.md#extension-members)
- [Null-conditional assignment](./csharp-14.md#null-conditional-assignment)
- [`nameof` supports unbound generic types](./csharp-14.md#unbound-generic-types-and-nameof)
