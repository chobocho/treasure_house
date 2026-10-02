// 슬라이드 p9-v8-proppat-ext10 — 확장 속성 패턴, C# 10
using System;

class City { public string Name; }
class Customer { public City Home; }

class App
{
    static void Main()
    {
        var c = new Customer { Home = new City { Name = "Seoul" } };
        // C# 8.0: nested braces
        Console.WriteLine(c is { Home: { Name: "Seoul" } });
        // C# 10: a dotted member path in one subpattern
        Console.WriteLine(c is { Home.Name: "Seoul" });
        var empty = new Customer();
        Console.WriteLine(empty is { Home.Name: "Seoul" });
    }
}
