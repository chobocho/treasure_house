// 슬라이드 p9-v8-as-errors — 비동기 스트림의 규칙, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Gen()
    {
        await Task.Yield();
        yield return 1;
    }

    static void NotAsync()
    {
        await foreach (int i in Gen()) { }           // needs async
    }

    static IAsyncEnumerable<int> NoAsync()
    {
        yield return 1;                              // needs async
    }

    static async IAsyncEnumerable<int> NoYield()
    {
        await Task.Yield();                          // needs a yield
    }

    static async IAsyncEnumerable<int> Catch()
    {
        try { yield return 1; }                      // still CS1626
        catch (Exception) { }
        await Task.Yield();
    }

    static void Main() { }
}
