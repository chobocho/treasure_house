// 슬라이드 p6-v5-split — await 가 메서드를 둘로 나눈다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // Main completes this task itself: same order every run
    static TaskCompletionSource<int> gate =
        new TaskCompletionSource<int>();

    static async Task<int> Work()
    {
        Console.WriteLine("Work: start");
        int x = await gate.Task;        // suspends and returns here
        Console.WriteLine("Work: resumed with " + x);
        return x * 2;
    }

    static void Main()
    {
        Console.WriteLine("Main: call");
        Task<int> t = Work();
        Console.WriteLine("Main: got " + t.Status);
        gate.SetResult(21);             // the second half runs here
        Console.WriteLine("Main: now " + t.Status);
        Console.WriteLine("Main: result " + t.Result);
    }
}
