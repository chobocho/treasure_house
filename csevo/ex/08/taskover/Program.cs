// 슬라이드 p8-v7-tasktype-over — 작업 같은 형식과 오버로드, C# 7.0
using System;
using System.Threading.Tasks;

class App
{
    static void Run(Func<Task> f) => Console.WriteLine("Task");
    static void Run(Func<ValueTask> f) =>
        Console.WriteLine("ValueTask");

    static void Get(Func<Task<int>> f) =>
        Console.WriteLine("Task<int>");
    static void Get(Func<Task<object>> f) =>
        Console.WriteLine("Task<object>");

    static void Main()
    {
        Get(async () => 1);       // exact match for Task<int>
        Run(() => Task.CompletedTask);
#if BAD
        Run(async () => { });     // exact for both task types
#endif
    }
}
