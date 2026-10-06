// 슬라이드 p14-v13-ru-break — 반대쪽: 이제 await 가 된다, C# 13.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

unsafe class C                         // unsafe context
{
    public IEnumerable<int> M()        // iterator: safe context
    {
        yield return 1;
        Run().Wait();
        yield return 3;

        async Task Run()               // inherits it
        {
            await Task.Yield();
            Console.WriteLine(2);
        }
    }
}

class App
{
    static void Main()
    {
        foreach (int v in new C().M()) Console.WriteLine(v);
    }
}
