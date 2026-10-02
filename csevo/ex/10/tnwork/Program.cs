// 슬라이드 p10-v9-tn-work — 뜻밖에 되는 대상 형식 new, C# 9.0
using System;

enum Color { Red, Green }

class App
{
    static void Main()
    {
        int? n = new();                // new int(), not null
        Console.WriteLine(n.HasValue + " " + n);
        (int a, int b) t = new();      // new ValueTuple<int, int>()
        Console.WriteLine(t);
        Color c = new();               // default(Color)
        Console.WriteLine(c);
        object o = new();
        Console.WriteLine(o.GetType());
        try
        {
            throw new();               // target: System.Exception
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType());
        }
    }
}
