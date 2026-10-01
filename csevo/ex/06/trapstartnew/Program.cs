// 슬라이드 p6-v5-trap-startnew — StartNew 와 async 람다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static TaskCompletionSource<int> gate =
        new TaskCompletionSource<int>();

    static async Task<int> Body()
    {
        await gate.Task;
        return 7;
    }

    static void Main()
    {
        // StartNew does not know about async: Task<Task<int>>
        Task<Task<int>> outer = Task.Factory.StartNew(() => Body());
        outer.Wait();
        Console.WriteLine("StartNew: outer " + outer.Status
            + ", inner " + outer.Result.Status);

        // Task.Run unwraps: one Task<int> that ends with Body
        Task<int> run = Task.Run(() => Body());
        Console.WriteLine("Task.Run: " + run.Wait(200));
        gate.SetResult(0);
        Console.WriteLine("after SetResult: " + run.Result
            + ", inner " + outer.Result.Result);
    }
}
