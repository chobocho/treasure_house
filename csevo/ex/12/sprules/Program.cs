// 슬라이드 p12-v11-spanpat-rules — 스팬 패턴의 경계, C# 11.0
using System;

class App
{
    static void Main()
    {
        ReadOnlySpan<char> none = default;
        ReadOnlySpan<char> empty = "".AsSpan();
        Console.WriteLine((none is "") + " " + (empty is ""));
        Console.WriteLine(none.IsEmpty + " " + (none == empty));
#if NULL
        Console.WriteLine(none is null);
#endif
#if STRNULL
        Console.WriteLine(none is (string)null);
#endif
    }
#if GENERIC
    static bool Is123<T>(Span<T> s) => s is "123";
#endif
#if TYPED
    static bool IsAbc<T>(Span<T> s) => s is Span<char> and "ABC";
#endif
}
