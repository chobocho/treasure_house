// 슬라이드 p11-v10-ih-assert — Debug.Assert 의 처리기, C# 10.0
#define DEBUG
using System;
using System.Diagnostics;

class Print : TraceListener        // report failures instead of exiting
{
    public override void Fail(string message, string detail)
        => Console.WriteLine("  assert failed: " + message);
    public override void Write(string s) { }
    public override void WriteLine(string s) { }
}

class App
{
    static int calls;
    static string Dump(int x) { calls++; return "x is " + x; }

    static void Check(int x)
    {
        Debug.Assert(x > 0, $"{Dump(x)}");
        Console.WriteLine($"  Check({x}): Dump ran {calls} time(s)");
    }

    static void Main()
    {
        Trace.Listeners.Clear();
        Trace.Listeners.Add(new Print());
        Check(5);
        Check(5);
        Check(-1);
        string msg = $"{Dump(7)}";          // built before the call
        Debug.Assert(true, msg);
        Console.WriteLine($"  via a string local: Dump ran {calls}");
    }
}
