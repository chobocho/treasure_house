// 슬라이드 p9-v8-nrt-noreturn — DoesNotReturn·DoesNotReturnIf, C# 8.0
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

class App
{
    [DoesNotReturn]
    static void Fail(string msg) =>
        throw new InvalidOperationException(msg);

    static void Check([DoesNotReturnIf(false)] bool ok, string msg)
    {
        if (!ok) throw new ArgumentException(msg);
    }

    static int A(string? s)
    {
        if (s == null) Fail("no s");
        return s.Length;                     // no warning
    }

    static int B(string? s)
    {
        Check(s != null, "no s");
        return s.Length;                     // no warning
    }

    static void Main()
    {
        Console.WriteLine(A("abc") + B("de"));
        try { A(null); }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
