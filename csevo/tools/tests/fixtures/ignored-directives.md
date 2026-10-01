# Ignored directives for file-based apps

[!INCLUDE[Specletdisclaimer](../speclet-disclaimer.md)]

Champion issue: <https://github.com/dotnet/csharplang/issues/8617>

## Summary

Add `#:` directive prefix to be used by tooling, but ignored by the language.

```cs
#!/usr/bin/dotnet run
#:sdk      Microsoft.NET.Sdk.Web
#:property TargetFramework=net11.0
#:property LangVersion=preview
#:package  System.CommandLine@2.0.0-*

Console.WriteLine("Hello, World!");
```

