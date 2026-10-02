// 슬라이드 p9-v8-dim-why — 공개한 인터페이스에 멤버 더하기, C# 8.0
using System;

// version 1 of a library interface
interface ILogger
{
    void Log(string message);
#if V2
    void LogError(string message);      // added in version 2
#endif
}

// a user's class, written against version 1
class ConsoleLogger : ILogger
{
    public void Log(string message) => Console.WriteLine(message);
}

class App
{
    static void Main()
    {
        ILogger log = new ConsoleLogger();
        log.Log("started");
    }
}
