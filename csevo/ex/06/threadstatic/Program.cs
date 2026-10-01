// 슬라이드 p6-v5-threadstatic — await 와 스레드 로컬, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    [ThreadStatic] static int requestId;

    static async Task Handle()
    {
        requestId = 7;
        Console.WriteLine("before await: requestId " + requestId);
        await Task.Delay(10);           // resumes on a pool thread
        Console.WriteLine("after await:  requestId " + requestId);
    }

    static void Main()
    {
        Handle().Wait();                // Main's thread is blocked here
        Console.WriteLine("Main's thread: requestId " + requestId);
    }
}
