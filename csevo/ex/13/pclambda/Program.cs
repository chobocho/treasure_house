// 슬라이드 p13-v12-pc-lambda — 람다와 메서드가 한 변수를, C# 12.0
using System;

class Seq(int p)
{
    public Func<int> F = () => p++;     // lambda in an initializer
    public int M() => p++;              // instance method
}

class App
{
    static void Main()
    {
        var s = new Seq(10);
        Console.WriteLine($"{s.F()} {s.M()} {s.F()} {s.M()}");
    }
}
