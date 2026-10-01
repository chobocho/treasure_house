// 슬라이드 p6-v5-configawait — ConfigureAwait(false), C# 5.0
using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;

// Single-threaded context: Post queues, Run drains in order
class Loop : SynchronizationContext
{
    readonly BlockingCollection<Action> q =
        new BlockingCollection<Action>();
    public int Posts;
    public override void Post(SendOrPostCallback d, object s)
    {
        Interlocked.Increment(ref Posts);
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
    static async Task Work(bool capture)
    {
        await Task.Delay(10).ConfigureAwait(capture);
        bool loop = SynchronizationContext.Current is Loop;
        Console.WriteLine("ConfigureAwait(" + capture + "): context is "
            + (loop ? "Loop" : "none"));
    }

    static void RunOnLoop(bool capture)
    {
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        loop.Run(Work(capture));
        Console.WriteLine("  posts to Loop: " + loop.Posts);
    }

    static void Main() { RunOnLoop(true); RunOnLoop(false); }
}
