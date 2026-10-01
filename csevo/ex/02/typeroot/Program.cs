// 슬라이드 p2-v1-runtime — 모든 형식의 뿌리 System.Object, C# 1.0
using System;
using System.Collections;

enum Color { Red, Green }
struct Point { public int X; public Point(int x) { X = x; } }

class App
{
    static void Chain(object o)
    {
        string line = "";
        Type t = o.GetType();
        while (t != null)
        {
            line += (line.Length == 0 ? "" : " -> ") + t.Name;
            t = t.BaseType;
        }
        Console.WriteLine(line);
    }

    static void Main()
    {
        Chain(42);
        Chain(3.5m);
        Chain(new Point(1));
        Chain(Color.Green);
        Chain("text");
        Chain(new int[3]);
        Chain(new ArrayList());
        Console.WriteLine(typeof(object).BaseType == null);
    }
}
