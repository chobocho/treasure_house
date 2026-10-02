// 슬라이드 p9-v8-dim-add — 기본 인터페이스 메서드, C# 8.0
using System;

interface ILogger
{
    void Log(string message);

    // version 2: a member with a body — the default implementation
    void LogError(string message) => Log("error: " + message);
}

// unchanged since version 1
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
        log.LogError("disk full");
    }
}
