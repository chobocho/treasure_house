// 슬라이드 p3-v2-partial-gate — partial 형식, C# 2.0
using System;

partial class Customer               // the hand-written part
{
    public string Greet() { return "Hello, " + Name; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Customer().Greet());
    }
}
