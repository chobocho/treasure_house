// 슬라이드 p13-v12-ce-over — 오버로드 해석: 스팬이 배열보다 낫다, C# 12
using System;

class Program
{
    static void P(string s) => Console.WriteLine(s);

    static void Generic<T>(Span<T> v) { P("Span<T>"); }
    static void Generic<T>(T[] v) { P("T[]"); }

    static void SpanDerived(Span<string> v) { P("Span"); }
    static void SpanDerived(object[] v) { P("obj[]"); }

    static void ArrayDerived(Span<object> v) { P("Span"); }
    static void ArrayDerived(string[] v) { P("str[]"); }

    static void Main()
    {
        Generic(new[] { "" });      // array initializer
        Generic([""]);              // collection expression
        SpanDerived([""]);
#if BAD
        SpanDerived(new[] { "" });
#endif
#if BAD2
        ArrayDerived([""]);
#endif
        ArrayDerived(new[] { "" });
    }
}
