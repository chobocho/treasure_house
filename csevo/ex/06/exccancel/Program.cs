// 슬라이드 p6-v5-exc-cancel — 취소는 실패와 다른 상태, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async Task<int> Step(CancellationToken ct, bool fail)
    {
        await Task.FromResult(0);
        if (fail) throw new InvalidOperationException("x");
        ct.ThrowIfCancellationRequested();
        return 1;
    }

    static void Show(string name, Task<int> t)
    {
        string inner = t.Exception == null ? "-"
            : t.Exception.InnerException.GetType().Name;
        Console.WriteLine("{0,-9} {1,-15} {2}", name, t.Status, inner);
    }

    static void Main()
    {
        CancellationTokenSource cts = new CancellationTokenSource();
        Show("ok", Step(cts.Token, false));
        Show("failed", Step(cts.Token, true));
        cts.Cancel();                   // by a call, no timer
        Task<int> c = Step(cts.Token, false);
        Show("canceled", c);
        try { c.GetAwaiter().GetResult(); }
        catch (OperationCanceledException e)
        {
            Console.WriteLine("await-style: " + e.GetType().Name);
        }
    }
}
