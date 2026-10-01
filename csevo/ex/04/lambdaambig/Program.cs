// 슬라이드 p4-v3-lambda-ambig — 본문으로도 못 고르면 모호하다, C# 3.0
using System;

class App
{
    static void Run(Func<int, int> f) { Console.WriteLine("int"); }
    static void Run(Func<string, int> f)
    {
        Console.WriteLine("string");
    }

    static void Main()
    {
        Run(x => 1);                 // fits both
        Run(x => x.Length);          // only string has Length
        Run((int x) => 1);           // explicit type picks one
    }
}
