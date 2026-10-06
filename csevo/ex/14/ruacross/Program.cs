// 슬라이드 p14-v13-ru-across — await·yield 를 넘으면 거절, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static int[] data = { 1, 2, 3 };

    static async Task<int> Async(string text)
    {
        ReadOnlySpan<char> s = text.AsSpan();
        ref int r = ref data[0];
        int n = s.Length + r;
        await Task.Yield();
#if SPAN
        n += s.Length;                // s used after await
#elif REF
        n += r;                       // r used after await
#endif
        return n;
    }

    static IEnumerable<int> Iter(string text)
    {
        ReadOnlySpan<char> s = text.AsSpan();
        yield return s.Length;
#if YIELD
        yield return s[0];            // s used after yield
#endif
    }

    static void Main()
    {
        Console.WriteLine(Async("abc").Result);
        foreach (int x in Iter("xyz")) Console.WriteLine(x);
    }
}
