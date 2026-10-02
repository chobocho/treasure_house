// 슬라이드 p5-v4-opt-exprtree — 뒤 버전: 식 트리 안에서, C# 14.0
using System;
using System.Linq.Expressions;

class Program
{
    public static string Greet(string name, string greeting = "Hello")
    {
        return greeting + ", " + name;
    }

    static void Main()
    {
        Expression<Func<string>> e1 = () => Greet("Ada");
        Expression<Func<string>> e2 = () => Greet(name: "Bo",
                                                  greeting: "Hi");
        Console.WriteLine(e1);
        Console.WriteLine(e2);
        Console.WriteLine(e1.Compile()() + " / " + e2.Compile()());
#if BAD
        Expression<Func<string>> e3 = () => Greet(greeting: "Hi",
                                                  name: "Cy");
#endif
    }
}
