// 슬라이드 p6-v5-awaitusing — using 블록과 await, C# 5.0
using System;
using System.Threading.Tasks;

class Res : IDisposable
{
    readonly string name;
    public Res(string name)
    {
        this.name = name;
        Console.WriteLine("  open " + name);
    }
    public void Dispose() { Console.WriteLine("  dispose " + name); }
}

class App
{
    static TaskCompletionSource<int> gate =
        new TaskCompletionSource<int>();

    static async Task Work()
    {
        using (new Res("file"))
        {
            await gate.Task;
            Console.WriteLine("  resumed inside using");
        }
    }

    static void Main()
    {
        Task t = Work();
        Console.WriteLine("Work returned: not disposed yet");
        gate.SetResult(0);
        Console.WriteLine("status " + t.Status);
    }
}
