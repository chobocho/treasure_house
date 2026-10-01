// 슬라이드 p3-v2-lifted-user — 직접 만든 연산자도 끌어올려진다, C# 2.0
using System;

struct Money
{
    public readonly int Cents;
    public Money(int cents) { Cents = cents; }

    public static Money operator +(Money a, Money b)
    {
        return new Money(a.Cents + b.Cents);
    }

    public override string ToString() { return Cents + "c"; }
}

class App
{
    static void Main()
    {
        Money? a = new Money(150);
        Money? b = new Money(250);
        Money? none = null;
        Money? sum = a + b;               // Money? + Money? : lifted
        Console.WriteLine(sum);
        Console.WriteLine((a + none).HasValue);
    }
}
