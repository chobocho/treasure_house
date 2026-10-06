// 슬라이드 p14-v13-lk-async — async 메서드 안의 lock (Lock), C# 13
using System;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static readonly Lock gate = new();
    static int n;

    static async Task<int> AddAsync()
    {
        await Task.Yield();
        lock (gate)                     // no await inside: allowed
        {
            n++;
#if AWAIT
            await Task.Yield();         // await inside the lock
#endif
        }
#if USING
        using (gate.EnterScope())       // the same, written by hand
        {
            await Task.Yield();
        }
#endif
        return n;
    }

    static async Task Main() =>
        Console.WriteLine(await AddAsync());
}
