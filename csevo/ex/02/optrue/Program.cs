// 슬라이드 p2-v1-optrue — operator true/false 와 &&, C# 1.0
using System;

class Check
{
    public bool Ok; public string Name;
    public Check(string n, bool ok) { Name = n; Ok = ok; }

    public static bool operator true(Check c)
    {
        Console.WriteLine("  true(" + c.Name + ")"); return c.Ok;
    }
    public static bool operator false(Check c)
    {
        Console.WriteLine("  false(" + c.Name + ")"); return !c.Ok;
    }
    public static Check operator &(Check a, Check b)
    {
        Console.WriteLine("  &(" + a.Name + ", " + b.Name + ")");
        return new Check(a.Name + b.Name, a.Ok && b.Ok);
    }
}

class App
{
    static void Main()
    {
        Check a = new Check("A", false), b = new Check("B", true);
        Console.WriteLine("if (b):");
        if (b) Console.WriteLine("  -> b is true");
        Console.WriteLine("a && b:");
        Check r = a && b;                     // false(a) only: skips &
        Console.WriteLine("  -> " + r.Name);
        Console.WriteLine("b && a:");
        r = b && a;                           // false(b), then &(b, a)
        Console.WriteLine("  -> " + r.Name);
    }
}
