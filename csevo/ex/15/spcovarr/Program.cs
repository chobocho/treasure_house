// 슬라이드 p15-v14-span-break — 공변 배열과 Span 판, C# 14
using System;
using System.Collections.Generic;
using System.Linq;

static class C
{
    public static string R<T>(IEnumerable<T> e) => "IEnumerable";
    public static string R<T>(Span<T> s) => "Span";
#if RO
    public static string R<T>(ReadOnlySpan<T> s) => "ReadOnlySpan";
#endif
}

class Program
{
    static void Main()
    {
        string[] s = ["a"];
        object[] o = s;                      // array covariance
        Console.WriteLine(C.R(s));
        Console.WriteLine(C.R(o.AsEnumerable()));   // workaround
        try { Console.WriteLine(C.R(o)); }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
