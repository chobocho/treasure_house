// 슬라이드 p6-v5-caller-over — 오버로드 해석은 모른 척, C# 5.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Log(string msg)
    {
        Console.WriteLine("Log(msg)       " + msg);
    }

    static void Log(string msg, [CallerMemberName] string m = "")
    {
        Console.WriteLine("Log(msg, m)    " + msg + " <- " + m);
    }

    static void Trace(object o)
    {
        Console.WriteLine("Trace(object)  " + o);
    }

    static void Trace(string s, [CallerLineNumber] int line = 0)
    {
        Console.WriteLine("Trace(string)  " + s + " line " + line);
    }

    static void Main()
    {
        Log("a");
        Log("b", "Main");
        Trace("c");
    }
}
