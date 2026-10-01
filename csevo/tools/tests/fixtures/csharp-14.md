
The members in the first extension block are called as though they're instance members of `IEnumerable<TSource>`, for example `sequence.IsEmpty`. The members in the second extension block are called as though they're static members of `IEnumerable<TSource>`, for example `IEnumerable<int>.Identity`.

You can learn more details by reading the article on [extension members](../programming-guide/classes-and-structs/extension-methods.md) in the programming guide, the language reference article on the [`extension` keyword](../language-reference/keywords/extension.md), and the [feature specification](~/_csharplang/proposals/csharp-14.0/extensions.md) for the new extension members feature.

## The `field` keyword

The token `field` enables you to write a property accessor body without declaring an explicit backing field. The token `field` is replaced with a compiler synthesized backing field.

