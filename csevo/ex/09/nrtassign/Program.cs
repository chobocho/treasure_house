// 슬라이드 p9-v8-nrt-assign — null 을 넣는 세 가지 경고, C# 8.0
#nullable enable
using System;

class App
{
    static int Len(string s) => s.Length;

    static void Never()                   // compiled, never called
    {
        string? maybe = Environment.GetEnvironmentVariable("NONE");
        string a = maybe;                 // CS8600
        Len(maybe);                       // CS8604
        Len(null);                        // CS8625
        Console.WriteLine(a);
    }

    static void Main()
    {
        Console.WriteLine("warnings only: the program still runs");
    }
}
