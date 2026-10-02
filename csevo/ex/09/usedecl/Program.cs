// 슬라이드 p9-v8-usingdecl — using 선언, C# 8.0
using System;

class Res : IDisposable
{
    string name;
    public Res(string name)
    {
        this.name = name;
        Console.WriteLine("open " + name);
    }
    public void Dispose() => Console.WriteLine("dispose " + name);
}

class App
{
    static int Work()
    {
        using var a = new Res("a");
        using var b = new Res("b");
        using Res c = new Res("c"), d = new Res("d");
        Console.WriteLine("  body");
        return 42;                   // disposed after this is computed
    }

    static void Main()
    {
        Console.WriteLine("Work() = " + Work());
    }
}
