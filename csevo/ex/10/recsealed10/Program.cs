// 슬라이드 p10-v9-rec-sealed10 — 레코드의 sealed ToString, C# 10.0
using System;

record Money(decimal Amount, string Currency)
{
#if C9
    public override string ToString() =>         // C# 9: not sealed
#else
    public sealed override string ToString() =>
#endif
        Amount.ToString("0.00") + " " + Currency;
}

record Price(decimal Amount, string Currency, string Item)
    : Money(Amount, Currency);

class App
{
    static void Main()
    {
        Console.WriteLine(new Money(3.5m, "EUR"));
        Console.WriteLine(new Price(2m, "USD", "tea"));
    }
}
