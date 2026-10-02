// 슬라이드 p9-v8-as-manual — await foreach 를 풀어 쓰면, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Three()
    {
        try
        {
            for (int i = 1; i <= 3; i++)
            {
                await Task.Yield();
                yield return i;
            }
        }
        finally { Console.WriteLine("  finally in Three"); }
    }

    static async Task Main()
    {
        await foreach (int x in Three())
            Console.WriteLine("sugar  " + x);

        // what the compiler writes for the loop above
        IAsyncEnumerator<int> e = Three().GetAsyncEnumerator();
        try
        {
            while (await e.MoveNextAsync())
            {
                int x = e.Current;
                Console.WriteLine("manual " + x);
            }
        }
        finally { await e.DisposeAsync(); }
    }
}
