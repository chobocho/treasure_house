// 슬라이드 p10-v9-rec-fields — 보이지 않는 필드도 동등성에 든다, C# 9.0
using System;

record Account(string Owner)
{
    private int version;                     // not printed, compared
    public Account Touch() => this with { version = version + 1 };
}

class App
{
    static void Main()
    {
        var a = new Account("ann");
        var b = a.Touch();
        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(a.ToString() == b.ToString());
        Console.WriteLine(a == b);
    }
}
