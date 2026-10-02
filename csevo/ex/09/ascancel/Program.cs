// 슬라이드 p9-v8-as-cancel — 토큰 두 개는 하나로 합쳐진다, C# 8.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Ticks(
#if !BAD
        [EnumeratorCancellation]
#endif
        CancellationToken ct = default)
    {
        for (int i = 1; i <= 5; i++)
        {
            await Task.Yield();
            if (ct.IsCancellationRequested) { yield break; }
            yield return i;
        }
    }

    static async Task Run(string who)
    {
        var a = new CancellationTokenSource();   // passed to Ticks
        var b = new CancellationTokenSource();   // WithCancellation
        int last = 0;
        var stream = Ticks(a.Token).WithCancellation(b.Token);
        await foreach (int t in stream)
        {
            last = t;
            if (t == 2) (who == "a" ? a : b).Cancel();
        }
        Console.WriteLine("cancel {0} at 2 -> last {1}", who, last);
    }

    static async Task Main()
    {
        await Run("a");
        await Run("b");
    }
}
