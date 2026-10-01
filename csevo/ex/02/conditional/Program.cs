// 슬라이드 p2-v1-conditional — 호출이 사라지는 Conditional, C# 1.0
using System;
using System.Diagnostics;

class Log
{
    [Conditional("TRACE_ON")]
    public static void Trace(string s)
    {
        Console.WriteLine("trace: " + s);
    }
}

class App
{
    static int calls;
    static string Expensive() { calls++; return "state"; }

    static void Main()
    {
        Log.Trace(Expensive());          // call AND argument may vanish
        Console.WriteLine("Expensive() ran " + calls + " time(s)");
    }
}
