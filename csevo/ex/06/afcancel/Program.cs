// 슬라이드 p6-v5-after-cancel — [EnumeratorCancellation], C# 8.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Ticks(
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        for (int i = 1; ; i++)
        {
            await Task.Yield();
            ct.ThrowIfCancellationRequested();
            yield return i;
        }
    }

    static async Task Main()
    {
        CancellationTokenSource cts = new CancellationTokenSource();
        IAsyncEnumerable<int> given = Ticks();   // no token here
        try
        {
            await foreach (int t in given.WithCancellation(cts.Token))
            {
                Console.WriteLine("tick " + t);
                if (t == 2) cts.Cancel();
            }
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("canceled inside the iterator");
        }
    }
}
