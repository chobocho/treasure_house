// 슬라이드 p6-v5-after-stream — 비동기 스트림과 await foreach, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    // async + yield return: an async iterator.
    static async IAsyncEnumerable<int> Squares(int n)
    {
        for (int i = 1; i <= n; i++)
        {
            await Task.Yield();         // e.g. wait for the next page
            Console.WriteLine("  produce " + i);
            yield return i * i;
        }
    }

    static async Task Main()
    {
        await foreach (int sq in Squares(3))
        {
            Console.WriteLine("consume " + sq);
        }
    }
}
