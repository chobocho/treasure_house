// 슬라이드 p6-v5-after-cawait — 비동기 스트림의 ConfigureAwait, C# 8.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Items()
    {
        for (int i = 1; i <= 2; i++)
        {
            await Task.Yield();
            yield return i;
        }
    }

    static async Task Main()
    {
        // Neither call changes the stream; both wrap it in a struct.
        ConfiguredCancelableAsyncEnumerable<int> c =
            Items().ConfigureAwait(false)
                   .WithCancellation(CancellationToken.None);
        Type t = c.GetType();
        Console.WriteLine(t.Name + " struct: " + t.IsValueType
            + ", IAsyncEnumerable: "
            + typeof(IAsyncEnumerable<int>).IsAssignableFrom(t));
        await foreach (int x in c)
            Console.WriteLine("item " + x);
    }
}
