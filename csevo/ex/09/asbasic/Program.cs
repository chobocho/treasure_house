// 슬라이드 p9-v8-asyncstream — 비동기 반복기와 await foreach, C# 8.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class App
{
    // async + IAsyncEnumerable<T> + yield return
    static async IAsyncEnumerable<string> Pages(int count)
    {
        Console.WriteLine("  [Pages starts]");
        for (int p = 1; p <= count; p++)
        {
            await Task.Delay(1);          // e.g. one network request
            Console.WriteLine("  [page {0} arrived]", p);
            yield return "page-" + p;
        }
        Console.WriteLine("  [Pages ends]");
    }

    static async Task Main()
    {
        IAsyncEnumerable<string> pages = Pages(3);
        Console.WriteLine("Pages(3) returned; nothing ran yet");
        await foreach (string p in pages)
            Console.WriteLine("use " + p);
        Console.WriteLine("done");
    }
}
