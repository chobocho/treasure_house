// 슬라이드 p6-v5-after-break — 일찍 빠져나오면 DisposeAsync, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Numbers()
    {
        try
        {
            for (int i = 1; ; i++)
            {
                await Task.Yield();
                yield return i;
            }
        }
        finally
        {
            await Task.Yield();     // await in finally: since C# 6
            Console.WriteLine("finally in the iterator");
        }
    }

    static async Task Main()
    {
        await foreach (int n in Numbers())
        {
            Console.WriteLine("got " + n);
            if (n == 2) break;
        }
        Console.WriteLine("after the loop");
    }
}
