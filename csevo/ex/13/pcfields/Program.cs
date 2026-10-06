// 슬라이드 p13-v12-pc-initonly — 초기화에만 쓰면 포착 없음, C# 12.0
using System;
using System.Reflection;

class InitOnly(int a, int b)
{
    public int Sum { get; } = a + b;       // only initializers
}

class Captures(int a, int b)
{
    public int Sum => a + b;               // a member body
}

class Mixed(int a, int b)
{
    public int A { get; } = a;             // a: initializer only
    public int B2 => b * 2;                // b: captured
}

class App
{
    static void Show(Type t)
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic
                  | BindingFlags.Public;
        var fs = t.GetFields(flags);
        Console.Write($"{t.Name,-9} {fs.Length} field(s):");
        foreach (var f in fs) Console.Write(" " + f.Name);
        Console.WriteLine();
    }

    static void Main()
    {
        Show(typeof(InitOnly));
        Show(typeof(Captures));
        Show(typeof(Mixed));
    }
}
