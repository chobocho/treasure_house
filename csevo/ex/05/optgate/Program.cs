// 슬라이드 p5-v4-opt-gate — 선택적 매개변수, C# 4.0
using System;

class Program
{
    static void Log(string msg, string level = "info", int indent = 0)
    {
        Console.WriteLine(new string(' ', indent) + level + ": " + msg);
    }

    static void Main()
    {
        Log("start");
        Log("disk almost full", "warn");
        Log("detail", "debug", 4);
    }
}
