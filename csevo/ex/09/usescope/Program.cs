// 슬라이드 p9-v8-ud-scope — 둘러싼 블록이 끝날 때, C# 8.0
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
    static void Main()
    {
        using var outer = new Res("outer");
        for (int i = 0; i < 2; i++)
        {
            using var r = new Res("loop" + i);   // one per iteration
            Console.WriteLine("  body " + i);
        }
        if (outer != null)
        {
            using var inner = new Res("inner");
        }
        Console.WriteLine("  end of Main");
    }
}
