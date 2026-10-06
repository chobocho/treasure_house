// 슬라이드 p14-v13-ru-old — C# 12 까지 막혔던 것과 아니던 것, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static int[] data = { 1, 2, 3 };

    // a Span local in an iterator, not crossing yield
    static IEnumerable<int> Lengths(string text)
    {
        ReadOnlySpan<char> s = text.AsSpan();
        int n = s.Length;
        yield return n;
    }
#if REF
    static IEnumerable<int> Refs()
    {
        ref int r = ref data[0];      // a ref local in an iterator
        r++;
        yield return data[0];
    }
#elif ASYNC
    static async Task<int> Len(string text)
    {
        ReadOnlySpan<char> s = text.AsSpan();  // in an async method
        int n = s.Length;
        await Task.Yield();
        return n;
    }
#endif

    static void Main()
    {
        foreach (int n in Lengths("abcd")) Console.WriteLine(n);
    }
}
