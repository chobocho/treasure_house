// 슬라이드 p10-v9-with-valid — with 와 생성자의 검사, C# 9.0
using System;

static class Pct
{
    public static int Check(int x) => x is >= 0 and <= 100
        ? x : throw new ArgumentOutOfRangeException(nameof(x));
}

record Percent(int Value)
{
    // the check runs only when the primary constructor runs
    public int Value { get; init; } = Pct.Check(Value);
}

record Checked
{
    readonly int v;
    public int Value { get => v; init => v = Pct.Check(value); }
}

class App
{
    static void Main()
    {
        var p = new Percent(50);
        try { new Percent(200); }
        catch (ArgumentOutOfRangeException)
        {
            Console.WriteLine("ctor");
        }
        Console.WriteLine(p with { Value = 200 });   // no check
        var c = new Checked { Value = 50 };
        try { Console.WriteLine(c with { Value = 200 }); }
        catch (ArgumentOutOfRangeException)
        {
            Console.WriteLine("init");
        }
    }
}
