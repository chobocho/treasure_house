// 슬라이드 p6-v5-exc-wait — 동기로 기다리면 AggregateException, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Fail()
    {
        await Task.FromResult(0);
        throw new FormatException("bad");
    }

    static void Try(string how, Func<int> f)
    {
        try { f(); }
        catch (Exception e)
        {
            Console.WriteLine("{0,-26} {1}", how, e.GetType().Name);
        }
    }

    static void Main()
    {
        Task<int> t = Fail();
        Try("t.Result", () => t.Result);
        Try("t.Wait()", () => { t.Wait(); return 0; });
        Try("t.GetAwaiter().GetResult()",
            () => t.GetAwaiter().GetResult());
    }
}
