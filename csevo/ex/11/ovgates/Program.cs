// 슬라이드 p11-v10-gates-demo — 메서드 안의 C# 10 기능 여덟, C# 10.0
using System;

struct Pixel { public int X, Y; }

class App
{
    static void Main()
    {
        var p = new Pixel { X = 1, Y = 2 };
        var q = p with { Y = 5 };               // with on structs
        var a = new { Name = "ann", Age = 3 };
        var b = a with { Age = 4 };             // with on anonymous
        const string Who = "C#";
        const string Hi = $"hi {Who}";          // const interpolated
        var twice = (int x) => x * 2;           // inferred delegate
        var half = [Obsolete] (int x) => x / 2; // lambda attributes
        var one = object () => 1;               // lambda return type
        int n;
        (n, var m) = (1, 2);                    // mixed deconstruction
        var e = new Exception("x", new Exception("inner"));
        bool deep = e is { InnerException.Message: "inner" };
        Console.WriteLine(q.Y + " " + b.Age + " " + Hi + " " + twice(n)
            + " " + half(m) + " " + one() + " " + deep);
    }
}
