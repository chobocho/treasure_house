// 슬라이드 p6-v5-asynclocal — await 를 건너는 값, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    [ThreadStatic] static int perThread;
    static AsyncLocal<int> perFlow = new AsyncLocal<int>();

    static async Task Handle()
    {
        perThread = 7;
        perFlow.Value = 7;
        await Task.Delay(10);           // resumes on a pool thread
        Console.WriteLine("ThreadStatic after await: " + perThread);
        Console.WriteLine("AsyncLocal after await:   " + perFlow.Value);
    }

    static void Main()
    {
        Handle().Wait();
    }
}
