// 슬라이드 p14-v13-ru-trap — Span 을 foreach 하며 yield 하면, C# 13.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<char> Upper(string text)
    {
#if BAD
        foreach (char c in text.AsSpan())    // a ref struct loop
            yield return char.ToUpperInvariant(c);
#else
        for (int i = 0; i < text.Length; i++)
        {
            char c = text.AsSpan()[i];       // a fresh span each time
            yield return char.ToUpperInvariant(c);
        }
#endif
    }

    static void Main()
        => Console.WriteLine(string.Concat(Upper("span")));
}
