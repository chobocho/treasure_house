// 슬라이드 p6-v5-caller-wrap — 직접 넘긴 값과 감싼 메서드, C# 5.0
using System;
using System.Runtime.CompilerServices;

delegate void LogFn(string msg, [CallerMemberName] string m = "?");

class App
{
    static void Log(string msg, [CallerMemberName] string m = "?")
    {
        Console.WriteLine(msg + " <- " + (m ?? "(null)"));
    }

    // Wrong: the wrapper's own name is filled in.
    static void Info(string msg) { Log("info " + msg); }

    // Right: take the caller's name and pass it on.
    static void Warn(string msg, [CallerMemberName] string m = "?")
    {
        Log("warn " + msg, m);
    }

    static void Run()
    {
        Log("plain");
        Log("explicit", "Custom");
        Log("null", null);
        Info("a");
        Warn("b");
        LogFn f = Log;
        f("via delegate");
    }

    static void Main()
    {
        Run();
    }
}
