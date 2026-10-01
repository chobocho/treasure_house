// 슬라이드 p6-v5-yield — Task.Yield 는 일부러 멈춘다, C# 5.0
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
    static async Task Work(string name)
    {
        Console.WriteLine(name + ": before Yield");
        await Task.Yield();             // never reports completed
        Console.WriteLine(name + ": after Yield");
    }

    static void Main()
    {
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        Task all = Task.WhenAll(Work("A"), Work("B"));
        Console.WriteLine("Main: both returned");
        loop.Run(all);                  // second halves run only now
        Console.WriteLine("Main: " + all.Status);
    }
}
