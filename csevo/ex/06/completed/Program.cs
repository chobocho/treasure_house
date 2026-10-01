// 슬라이드 p6-v5-completed — 끝난 Task 는 멈추지 않는다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Sum(Task<int> a, Task<int> b)
    {
        Console.WriteLine("  Sum: start");
        int x = await a;
        Console.WriteLine("  Sum: got a");
        int y = await b;
        Console.WriteLine("  Sum: got b");
        return x + y;
    }

    static void Main()
    {
        // both already completed: await does not suspend
        Task<int> t = Sum(Task.FromResult(1), Task.FromResult(2));
        Console.WriteLine("Main: " + t.Status + " " + t.Result);

        // one incomplete task: suspends there
        TaskCompletionSource<int> late =
            new TaskCompletionSource<int>();
        Task<int> u = Sum(Task.FromResult(1), late.Task);
        Console.WriteLine("Main: " + u.Status);
        late.SetResult(5);
        Console.WriteLine("Main: " + u.Status + " " + u.Result);
    }
}
