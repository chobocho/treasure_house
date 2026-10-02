// 슬라이드 p8-v7-decon-order — 분해는 무엇으로 번역되나, C# 7.0
using System;

static class L
{
    public static void Log(string s) => Console.WriteLine("  " + s);
}

class Pair
{
    public void Deconstruct(out int a, out int b)
    {
        L.Log("Deconstruct");
        a = 1; b = 2;
    }
}

class Target
{
    public string Name;
    public int V
    {
        set { L.Log("set " + Name + "=" + value); }
    }
}

class App
{
    static Pair Make() { L.Log("Make"); return new Pair(); }
    static Target T(string n)
    {
        L.Log("target " + n);
        return new Target { Name = n };
    }

    static void Main()
    {
        (T("x").V, T("y").V) = Make();
        var r = (T("p").V, T("q").V) = Make();  // the value: a tuple
        Console.WriteLine(r);
    }
}
