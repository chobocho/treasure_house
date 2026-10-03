// 슬라이드 p11-v10-rs-sealed — 레코드의 sealed ToString, C# 10.0
using System;

record Money(decimal Amount)
{
    public sealed override string ToString() => Amount.ToString("0.00");
}

record Tip(decimal Amount, string Who) : Money(Amount)
{
#if BAD
    public override string ToString() => Who + " tipped";
#endif
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Tip(1.5m, "ann"));
        Console.WriteLine(new Tip(1.5m, "ann") == new Tip(1.5m, "bob"));
    }
}
