// 슬라이드 p6-v5-trap-whenall — WhenAll 의 예외 여럿, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task Fail(string name)
    {
        await Task.FromResult(0);
        throw new InvalidOperationException(name + " failed");
    }

    static async Task<string> Demo()
    {
        Task all = Task.WhenAll(Fail("a"), Fail("b"));
        try { await all; return "no exception"; }
        catch (Exception e)
        {
            Console.WriteLine("await threw: " + e.Message);
        }
        foreach (Exception e in all.Exception.InnerExceptions)
            Console.WriteLine("  in all.Exception: " + e.Message);
        return "status " + all.Status;
    }

    static void Main() { Console.WriteLine(Demo().Result); }
}
