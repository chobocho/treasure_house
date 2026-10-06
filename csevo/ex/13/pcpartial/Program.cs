// 슬라이드 p13-v12-pc-partial — partial 의 매개변수 목록, C# 12.0
using System;

partial class Money(decimal amount)
{
    public decimal Amount => amount;
}

partial class Money
{
    public Money Twice() => new(amount * 2);   // same parameter here
}

#if BAD
partial class Money(decimal amount) { }
#endif

class App
{
    static void Main() =>
        Console.WriteLine(new Money(2.5m).Twice().Amount);
}
