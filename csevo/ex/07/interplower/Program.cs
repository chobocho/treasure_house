// 슬라이드 p7-v6-interp-lower — 구멍의 평가와 ToString 의 차례, C# 6.0
using System;

class Loud
{
    readonly string name;
    public Loud(string name) { this.name = name; }
    public override string ToString()
    {
        Console.WriteLine("  ToString " + name);
        return name;
    }
}

class App
{
    static Loud Make(string name)
    {
        Console.WriteLine("  eval     " + name);
        return new Loud(name);
    }

    static void Main()
    {
        string s = $"{Make("a")}-{Make("b")}-{Make("c")}";
        Console.WriteLine(s);
    }
}
