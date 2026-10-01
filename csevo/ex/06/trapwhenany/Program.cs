// 슬라이드 p6-v5-trap-whenany — WhenAny 는 Task 를 돌려준다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<string> Demo()
    {
        TaskCompletionSource<int> a = new TaskCompletionSource<int>();
        TaskCompletionSource<int> b = new TaskCompletionSource<int>();
        Task<Task<int>> any = Task.WhenAny(a.Task, b.Task);

        b.SetException(new TimeoutException("b timed out"));
        Task<int> first = await any;    // does not throw
        Console.WriteLine("winner is b? " + (first == b.Task)
            + ", " + first.Status);
        Console.WriteLine("a still " + a.Task.Status);
        try { return "value " + await first; }
        catch (TimeoutException e) { return "await: " + e.Message; }
    }

    static void Main() { Console.WriteLine(Demo().Result); }
}
