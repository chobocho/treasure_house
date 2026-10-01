// 슬라이드 p6-v5-trap-sync — 문맥 위에서 동기로 기다리기, C# 5.0
using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

// Single-threaded context: Post queues, Run drains in order
class Loop : SynchronizationContext
{
    readonly BlockingCollection<Action> q =
        new BlockingCollection<Action>();
    public override void Post(SendOrPostCallback d, object s)
    {
        q.Add(() => d(s));
    }
    public void Run(Task t)
    {
        t.ContinueWith(_ => q.CompleteAdding(), TaskScheduler.Default);
        foreach (Action a in q.GetConsumingEnumerable()) a();
    }
}

class App
{
    static async Task<int> Fetch()
    {
        await Task.Delay(10);
        return 42;
    }

    static async Task Caller()          // async all the way up
    {
        Console.WriteLine("await on Loop: " + await Fetch());
    }

    static void Main()
    {
        Console.WriteLine(".Result, no context: " + Fetch().Result);
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        Console.WriteLine("Wait on Loop: " + Fetch().Wait(500));
        loop.Run(Caller());
    }
}
