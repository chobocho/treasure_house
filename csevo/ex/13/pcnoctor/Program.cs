// 슬라이드 p13-v12-pc-noctor — 매개변수 없는 생성자가 사라진다, C# 12.0
using System;

class Plain { }
class Prim(int x) { public int X => x; }
class Empty() { }

class App
{
    static void Show(Type t)
    {
        Console.Write(t.Name + ":");
        foreach (var c in t.GetConstructors())
            Console.Write($" ({c.GetParameters().Length} params)");
        Console.WriteLine();
    }

    static void Main()
    {
        Show(typeof(Plain));
        Show(typeof(Prim));
        Show(typeof(Empty));
#if BAD
        var p = new Prim();
#endif
    }
}
