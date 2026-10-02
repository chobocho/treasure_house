// 슬라이드 p9-v8-nrt-attrbody — 특성은 메서드 몸체도 검사한다, C# 8.0
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

class App
{
    [return: NotNull]
    static string? Never() => null;          // CS8603

    [return: MaybeNull]
    static T Empty<T>() => default;          // no warning in the body

    static void Read([DisallowNull] string? p)
    {
        Console.WriteLine(p.Length);         // p assumed not null
    }

    static void Main()
    {
        Read("abc");
        Console.WriteLine(Empty<string>() == null);
        Console.WriteLine(Never() == null);
    }
}
