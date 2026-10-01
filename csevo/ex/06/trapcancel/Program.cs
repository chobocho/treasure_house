// 슬라이드 p6-v5-trap-cancel — 취소는 협조다, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async Task<int> Steps(CancellationToken ct,
        Action<int> onStep)
    {
        int done = 0;
        for (int i = 1; i <= 5; i++)
        {
            ct.ThrowIfCancellationRequested();  // the only checkpoint
            await Task.Delay(1);
            done = i;
            onStep(i);
        }
        return done;
    }

    static void Main()
    {
        CancellationTokenSource cts = new CancellationTokenSource();
        Task<int> t = Steps(cts.Token, i =>
        {
            Console.WriteLine("step " + i);
            if (i == 2) cts.Cancel();   // asks; does not stop step 2
        });
        try { Console.WriteLine("done " + t.Result); }
        catch (AggregateException e)
        {
            Console.WriteLine(e.InnerException.GetType().Name
                + ", status " + t.Status);
        }
    }
}
