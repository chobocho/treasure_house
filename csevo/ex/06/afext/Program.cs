// 슬라이드 p6-v5-after-ext — 확장 메서드 GetAsyncEnumerator, C# 9.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

static class Ext
{
    // Make a Task<int[]> usable in await foreach.
    public static async IAsyncEnumerator<int> GetAsyncEnumerator(
        this Task<int[]> pending)
    {
        foreach (int x in await pending) yield return x;
    }
}

class App
{
    static async Task<int[]> Load()
    {
        await Task.Yield();
        return new[] { 10, 20, 30 };
    }

    static async Task Main()
    {
        await foreach (int x in Load())
            Console.WriteLine("item " + x);
    }
}
