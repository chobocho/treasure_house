// 슬라이드 p9-v8-as-finally — break 하면 finally 가 await 된다, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Rows()
    {
        Console.WriteLine("  open cursor");
        try
        {
            for (int i = 1; i <= 100; i++)
            {
                await Task.Yield();
                yield return i;
            }
        }
        finally
        {
            await Task.Delay(1);         // await inside finally is fine
            Console.WriteLine("  close cursor (awaited)");
        }
    }

    static async Task Main()
    {
        await foreach (int r in Rows())
        {
            Console.WriteLine("row " + r);
            if (r == 2) break;           // -> DisposeAsync -> finally
        }
        Console.WriteLine("after the loop");
    }
}
