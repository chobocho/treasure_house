// 슬라이드 p8-v7_2-refstruct-capture — async·반복기, C# 7.2
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async Task<int> Later(Span<int> s)      // async parameter
    {
        await Task.Yield();
        return 0;
    }

    static IEnumerable<int> Iter(Span<int> s)      // iterator parameter
    {
        yield return 0;
    }

    static void Main() { }
}
