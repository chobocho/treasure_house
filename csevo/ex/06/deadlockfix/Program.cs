// 슬라이드 p6-v5-deadlock-fix — ConfigureAwait(false) 로 풀기, C# 5.0
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
    static async Task<int> LibraryCall()
    {
        await Task.Delay(10).ConfigureAwait(false);
        return 42;
    }

    static void Main()
    {
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        Task<int> t = LibraryCall();
        bool done = t.Wait(500);        // .Result would block forever
        Console.WriteLine("Wait(500) returned " + done);
        Console.WriteLine("status " + t.Status);
        loop.Run(t);                    // let the loop work
        Console.WriteLine("after Run: " + t.Status + " " + t.Result);
    }
}
