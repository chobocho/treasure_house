// 슬라이드 p9-v8-as-config — ConfigureAwait 와 WithCancellation, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Two()
    {
        await Task.Yield();
        yield return 1;
        yield return 2;
    }

    static async Task Main()
    {
        var cfg = Two().ConfigureAwait(false);
        var both = Two().WithCancellation(CancellationToken.None)
                        .ConfigureAwait(false);
        foreach (object o in new object[] { cfg, both })
        {
            Type t = o.GetType();
            Console.WriteLine("{0}  interfaces: {1}",
                t.Name, t.GetInterfaces().Length);
        }
        // not an IAsyncEnumerable<T>, still usable: pattern-based
        await foreach (int i in both)
            Console.WriteLine(i);
    }
}
