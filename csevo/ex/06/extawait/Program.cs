// 슬라이드 p6-v5-extawait — 확장 메서드 GetAwaiter, C# 5.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

static class AwaitExtensions
{
    // await on a list of tasks = await Task.WhenAll(list)
    public static TaskAwaiter<int[]> GetAwaiter(
        this IEnumerable<Task<int>> tasks)
    {
        return Task.WhenAll(tasks).GetAwaiter();
    }

    // await on a plain int, for the sake of it
    public static TaskAwaiter<int> GetAwaiter(this int x)
    {
        return Task.FromResult(x).GetAwaiter();
    }
}

class App
{
    static async Task<string> Demo()
    {
        List<Task<int>> list = new List<Task<int>>();
        list.Add(Task.FromResult(1));
        list.Add(Task.FromResult(2));
        int[] all = await list;
        int n = await 40;
        return string.Join("+", all) + " and " + n;
    }

    static void Main() { Console.WriteLine(Demo().Result); }
}
