// 슬라이드 p7-v6-overload — 메서드 그룹과 Task.Run, C# 6.0
using System;
using System.Threading.Tasks;

class Program
{
    static Task DoThings()
    {
        Console.WriteLine("doing things");
        return Task.FromResult(0);
    }

    static string Pick(Action a) { return "Action"; }
    static string Pick(Func<Task> f) { return "Func<Task>"; }

    static void Main()
    {
        Console.WriteLine(Pick(DoThings));
        Task.Run(DoThings).Wait();
    }
}
