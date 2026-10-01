// 슬라이드 p6-v5-trap-canceldelay — 토큰을 받는 API, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async Task<string> Wait(CancellationToken ct)
    {
        try
        {
            await Task.Delay(Timeout.Infinite, ct);  // forever, unless
            return "woke up";
        }
        catch (OperationCanceledException e)
        {
            return "canceled: " + e.GetType().Name;
        }
    }

    static void Main()
    {
        CancellationTokenSource cts = new CancellationTokenSource();
        Task<string> t = Wait(cts.Token);
        Console.WriteLine("waiting: " + t.Status);
        cts.Cancel();
        Console.WriteLine(t.Result);

        bool ran = false;               // already-canceled token
        Task r = Task.Run(() => { ran = true; }, cts.Token);
        try { r.Wait(); }
        catch (AggregateException) { }
        Console.WriteLine("Task.Run: " + r.Status + ", ran? " + ran);
    }
}
