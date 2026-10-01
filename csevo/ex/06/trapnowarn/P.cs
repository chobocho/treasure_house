// 슬라이드 p6-v5-trap-nowarn — 경고가 나는 곳과 안 나는 곳, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> CountAsync()
    {
        await Task.FromResult(0);
        return 3;
    }

    static async Task SaveAsync()
    {
        await Task.FromResult(0);
        throw new InvalidOperationException("save failed");
    }

    static void SyncCaller()
    {
        SaveAsync();                    // CS4014 here too
    }

    static async Task AsyncCaller()
    {
        var n = CountAsync();           // assigned: no CS4014
        Console.WriteLine("count: " + n);
        await Task.FromResult(0);
    }

    static void Main()
    {
        SyncCaller();
        AsyncCaller().Wait();
        Console.WriteLine("Main: no exception");
    }
}
