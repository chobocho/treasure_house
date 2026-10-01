// 슬라이드 p6-v5-trap-lambda — async 람다가 async void 가 될 때, C# 5.0
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
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
    static void Main()
    {
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        List<int> a = new List<int>(), b = new List<int>();
        List<int> xs = new List<int> { 1, 2, 3 };

        // ForEach takes Action<int>: each lambda is async void
        xs.ForEach(async x => { await Task.Yield(); a.Add(x); });
        Console.WriteLine("after ForEach: " + a.Count + " items");

        // Select keeps the Task: someone can wait for all of them
        Task all = Task.WhenAll(
            xs.Select(async x => { await Task.Yield(); b.Add(x); }));
        loop.Run(all);
        Console.WriteLine("after WhenAll: " + b.Count + " items");
    }
}
