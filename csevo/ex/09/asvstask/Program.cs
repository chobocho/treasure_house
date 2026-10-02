// 슬라이드 p9-v8-as-vstask — Task<List<T>> 와 견주면, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    // C# 7.3: the whole list, after the last await
    static async Task<List<int>> AllAtOnce()
    {
        var list = new List<int>();
        for (int i = 1; i <= 3; i++)
        {
            await Task.Delay(1);
            Console.WriteLine("  made " + i);
            list.Add(i);
        }
        return list;
    }

    // C# 8.0: one element at a time
    static async IAsyncEnumerable<int> OneByOne()
    {
        for (int i = 1; i <= 3; i++)
        {
            await Task.Delay(1);
            Console.WriteLine("  made " + i);
            yield return i;
        }
    }

    static async Task Main()
    {
        Console.WriteLine("Task<List<int>>:");
        foreach (int x in await AllAtOnce())
            Console.WriteLine("got " + x);
        Console.WriteLine("IAsyncEnumerable<int>:");
        await foreach (int x in OneByOne())
            Console.WriteLine("got " + x);
    }
}
