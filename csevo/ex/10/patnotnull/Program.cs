// 슬라이드 p10-v9-pat-notnull — is not null 과 != null, C# 9.0
using System;

class Money
{
    public decimal Amount { get; set; }

    // a "helpful" operator: any Money with Amount 0 equals null
    public static bool operator ==(Money a, Money b)
    {
        Console.Write("[op==] ");
        if (a is null || b is null) return (a ?? b)?.Amount == 0;
        return a.Amount == b.Amount;
    }
    public static bool operator !=(Money a, Money b) => !(a == b);
    public override bool Equals(object o) => o is Money m && m == this;
    public override int GetHashCode() => Amount.GetHashCode();
}

class App
{
    static void Main()
    {
        Money zero = new Money();
        Console.WriteLine("!= null     : " + (zero != null));
        Console.WriteLine("is not null : " + (zero is not null));
        Console.WriteLine("is object   : " + (zero is object));
    }
}
