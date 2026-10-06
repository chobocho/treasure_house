// 슬라이드 p14-v13-ru-param — 여전히 안 되는 것: 매개변수, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
#if ASYNC
    static async Task<int> Len(ReadOnlySpan<char> s)   // parameter
    {
        await Task.Yield();
        return s.Length;
    }
#elif ITER || UNUSED
    static IEnumerable<int> Items(Span<int> s)          // parameter
    {
#if ITER
        yield return s.Length;                          // used
#else
        yield return 0;                                 // unused
#endif
    }
#endif
    // the C# 13 way: take a string, make the span inside
    static async Task<int> Len(string text)
    {
        await Task.Yield();
        return text.AsSpan().Trim().Length;
    }

    static void Main()
    {
        Console.WriteLine(Len("  ab  ").Result);
#if UNUSED
        foreach (int x in Items(new int[3])) Console.WriteLine(x);
#endif
    }
}
