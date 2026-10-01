// 슬라이드 p3-v2-partial-why — 사람이 쓴 쪽 파일, C# 1.0
using System;

class Customer                       // the same class, by hand
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
