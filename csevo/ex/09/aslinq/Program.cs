// 슬라이드 p9-v8-as-linq — .NET 10 의 AsyncEnumerable, C# 8.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

class App
{
    static async IAsyncEnumerable<int> Numbers()
    {
        for (int i = 1; i <= 6; i++)
        {
            await Task.Yield();
            yield return i;
        }
    }

    static async Task Main()
    {
        int[] evens = await Numbers()
            .Where(n => n % 2 == 0)
            .Select(n => n * 10)
            .ToArrayAsync();
        Console.WriteLine(string.Join(",", evens));
        Type t = typeof(AsyncEnumerable);
        Console.WriteLine("{0} [{1}]", t.FullName,
            t.Assembly.GetName().Name);
    }
}
