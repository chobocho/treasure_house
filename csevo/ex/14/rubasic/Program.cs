// 슬라이드 p14-v13-refasync — async·반복기 안의 Span 지역 변수, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async Task<int> Checksum(string text)
    {
        await Task.Yield();
        ReadOnlySpan<char> s = text.AsSpan(1);   // ref struct local
        Span<int> acc = stackalloc int[1];       // stack memory
        foreach (char c in s) acc[0] += c;
        int sum = acc[0];                        // copy out
        await Task.Yield();
        return sum;
    }

    static IEnumerable<int> WordLengths(string text)
    {
        int start = 0;
        while (start < text.Length)
        {
            ReadOnlySpan<char> rest = text.AsSpan(start);
            int sp = rest.IndexOf(' ');
            int len = sp < 0 ? rest.Length : sp;
            start += len + 1;
            yield return len;                    // rest: not used after
        }
    }

    static void Main()
    {
        Console.WriteLine(Checksum("xABC").Result);
        var lens = WordLengths("ref in async");
        Console.WriteLine(string.Join(",", lens));
    }
}
