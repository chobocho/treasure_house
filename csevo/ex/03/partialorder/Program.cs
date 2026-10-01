// 슬라이드 p3-v2-partial-order — 조각 사이의 초기화 차례, C# 2.0
using System;

partial class Config
{
    public static string P = Config.Log("Program.cs field");

    public static string Log(string what)
    {
        Console.WriteLine("init " + what);
        return what;
    }

    static Config() { Console.WriteLine("static ctor"); }
}

class App
{
    static void Main()
    {
        Console.WriteLine("first use: " + Config.P);
    }
}
