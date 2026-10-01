// 슬라이드 p6-v5-sm-hand — 손으로 쓴 판과 컴파일러의 판, C# 5.0
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    public static TaskCompletionSource<int> Gate;

    static Task<int> AddLaterByHand(int a, int b)   // the stub
    {
        Machine m = new Machine();
        m.a = a; m.b = b; m.state = -1;
        m.builder = AsyncTaskMethodBuilder<int>.Create();
        m.builder.Start(ref m);         // runs MoveNext once, right now
        return m.builder.Task;
    }

    static async Task<int> AddLater(int a, int b)   // the source
    {
        Console.WriteLine("  start");
        int bonus = await Gate.Task;
        Console.WriteLine("  resumed, bonus " + bonus);
        return a + b + bonus;
    }

    static void Run(string name, Func<int, int, Task<int>> f)
    {
        Console.WriteLine(name);
        Gate = new TaskCompletionSource<int>();
        Task<int> t = f(2, 3);
        Console.WriteLine("  returned: " + t.Status);
        Gate.SetResult(10);
        Console.WriteLine("  result " + t.Result);
    }

    static void Main()
    {
        Run("by hand", AddLaterByHand);
        Run("compiler", AddLater);
    }
}
