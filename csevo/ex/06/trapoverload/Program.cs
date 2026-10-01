// 슬라이드 p6-v5-trap-overload — Action 과 Func<Task> 사이, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static TaskCompletionSource<int> gate;

    static void Run(Action a) { Console.WriteLine("Run(Action)"); a(); }
    static void Run(Func<Task> f)
    {
        Console.WriteLine("Run(Func<Task>)");
        f();
    }
    static void OnlyAction(Action a)
    {
        Console.WriteLine("OnlyAction(Action)");
        a();
    }

    static void Main()
    {
        Run(() => Console.WriteLine("  sync lambda"));
        Run(async () => { await Task.FromResult(0); });

        gate = new TaskCompletionSource<int>();
        OnlyAction(async () =>          // compiles: async void lambda
        {
            await gate.Task;
            Console.WriteLine("  async lambda finished");
        });
        Console.WriteLine("OnlyAction returned");
        gate.SetResult(0);
    }
}
