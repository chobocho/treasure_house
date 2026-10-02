// 슬라이드 p5-v4-gates — C# 4 의 네 게이트를 한 파일에, C# 4.0
using System;

interface ISource<out T>                 // type variance
{
    T Get();
}

class Box : ISource<string>
{
    public string Get() { return "box"; }
}

class Program
{
    // optional parameter
    static string Greet(string name, string greeting = "Hello")
    {
        return greeting + ", " + name;
    }

    static void Main()
    {
        ISource<object> src = new Box();
        dynamic d = src.Get();                   // dynamic
        Console.WriteLine(d.Length);
        Console.WriteLine(Greet("C# 4"));
        Console.WriteLine(Greet(greeting: "Hi", name: "Anders"));
    }
}
