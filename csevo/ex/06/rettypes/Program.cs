// 슬라이드 p6-v5-rettypes — async 메서드의 반환 형식 셋, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async void FireAndForget()
    {
        await Task.FromResult(0);
        Console.WriteLine("void: done");
    }

    static async Task NoValue()
    {
        await Task.FromResult(0);
        Console.WriteLine("Task: done");
    }

    static async Task<int> WithValue()
    {
        int x = await Task.FromResult(41);
        return x + 1;                   // an int, not a Task
    }

    static void Main()
    {
        FireAndForget();                // nothing comes back
        Task t = NoValue();
        Task<int> ti = WithValue();
        Console.WriteLine(t.GetType().Name + " " + t.Status);
        Console.WriteLine(ti.GetType().Name + " " + ti.Result);
    }
}
