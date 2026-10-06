// 슬라이드 p13-v12-pc-order — 기반 생성자보다 먼저 저장된다, C# 12.0
using System;

abstract class B
{
    protected B(string who) =>
        Console.WriteLine($"B({who}) sees {Peek()}");
    protected abstract int Peek();
}

class Old : B
{
    readonly int n;
    public Old(int n) : base("Old") { this.n = n; }
    protected override int Peek() => n;
}

class New(int n) : B("New")
{
    protected override int Peek() => n;      // captured
}

class Init(int n) : B(Log("base argument", "Init"))
{
    readonly int a = Log("initializer", 2 * n);
    protected override int Peek() => a;
    static T Log<T>(string s, T v) { Console.WriteLine(s); return v; }
}

class App
{
    static void Main()
    {
        new Old(5);
        new New(5);
        new Init(5);
    }
}
