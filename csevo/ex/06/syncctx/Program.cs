// 슬라이드 p6-v5-ctx — 이어 달리기는 문맥으로 돌아온다, C# 5.0
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
    static Thread main;

    static async Task Work(string tag)
    {
        await Task.Delay(10);           // completes on a timer thread
        Console.WriteLine(tag + ": on Main's thread? "
            + (Thread.CurrentThread == main));
    }

    static void Main()
    {
        main = Thread.CurrentThread;
        Work("no context").Wait();
        Loop loop = new Loop();
        SynchronizationContext.SetSynchronizationContext(loop);
        loop.Run(Work("Loop"));
        Console.WriteLine("posts to Loop: " + loop.Posts);
    }
}
