// 슬라이드 p6-v5-syncfirst — 첫 await 까지는 부른 스레드에서, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static Thread caller;

    static async Task Work()
    {
        // before the first await: still inside Main's call
        Console.WriteLine("before: caller thread? "
            + (Thread.CurrentThread == caller));
        await Task.Delay(20);           // incomplete task: returns here
        Console.WriteLine("after: on a pool thread? "
            + Thread.CurrentThread.IsThreadPoolThread);
    }

    static void Main()
    {
        caller = Thread.CurrentThread;
        Task t = Work();
        Console.WriteLine("Main: Work returned");
        t.Wait();
    }
}
