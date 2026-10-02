// 슬라이드 p9-v8-nrt-maybenull — MaybeNull 과 NotNull, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

class App
{
    // C# 8 cannot write T? for an unconstrained T: use the attribute
    [return: MaybeNull]
    static T FirstOrDefault<T>(List<T> xs) =>
        xs.Count > 0 ? xs[0] : default!;

    // after the call, s is not null, whatever it was before
    static void Ensure([NotNull] ref string? s)
    {
        if (s == null) s = "made";
    }

    static void Main()
    {
        string first = FirstOrDefault(new List<string>());  // CS8600
        Console.WriteLine(first == null);

        string? s = null;
        Ensure(ref s);
        Console.WriteLine(s.Length);         // no warning
    }
}
