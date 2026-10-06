// 슬라이드 p14-v13-or-lang — BCL 의 우선순위와 언어 버전, C# 13
#define TRACE
#define DEBUG
using System;
using System.Diagnostics;

class Show : TraceListener
{
    public override void Write(string m) { }
    public override void WriteLine(string m) { }
    public override void Fail(string m)
        => Console.WriteLine("Fail(\"" + m + "\")");
    public override void Fail(string m, string d)
        => Console.WriteLine("Fail(\"" + m + "\", \"" + d + "\")");
}

class Program
{
    static void Main()
    {
        Trace.Listeners.Clear();
        Trace.Listeners.Add(new Show());
        int n = 3;
        Trace.Assert(n > 5);
        Debug.Assert(n * 2 == 7);
    }
}
