// 슬라이드 p6-v5-awaitable — 무엇이든 await 할 수 있다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Use(Later l)
    {
        int v = await l;
        return v * 2;
    }

    static void Main()
    {
        Console.WriteLine("incomplete:");
        Later a = new Later();
        Task<int> t = Use(a);
        Console.WriteLine("  -- Use returned, completing");
        a.Complete(21);
        Console.WriteLine("  result " + t.Result);

        Console.WriteLine("already complete:");
        Later b = new Later();
        b.Complete(5);
        Console.WriteLine("  result " + Use(b).Result);
    }
}
