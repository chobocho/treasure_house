// 슬라이드 p6-v5-caller-members — 접근자·인덱서·초기화자, C# 5.0
using System;
using System.Runtime.CompilerServices;

interface IJob { void Run(); }

class Box : IJob
{
    static string N([CallerMemberName] string m = "?") { return m; }

    public string Tag = N();
    public int Size
    {
        get { Console.WriteLine("get    -> " + N()); return 0; }
        set { Console.WriteLine("set    -> " + N()); }
    }
    public int this[int i]
    {
        get { Console.WriteLine("index  -> " + N()); return i; }
    }
    public event EventHandler Changed
    { add { Console.WriteLine("add    -> " + N()); } remove { } }
    void IJob.Run() { Console.WriteLine("IJob   -> " + N()); }
    public void Gen<T>() { Console.WriteLine("Gen<T> -> " + N()); }
}

class App
{
    static void Main()
    {
        Box b = new Box();
        Console.WriteLine("field  -> " + b.Tag);
        int x = b.Size; b.Size = 1; x = b[0];
        b.Changed += null;
        ((IJob)b).Run();
        b.Gen<int>();
    }
}
