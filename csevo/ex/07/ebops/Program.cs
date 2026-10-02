// 슬라이드 p7-v6-eb-ops — 연산자와 변환도 =>, C# 6.0
using System;

struct Money
{
    public readonly int Cents;

    public Money(int cents)
    {
        Cents = cents;
    }

    public static Money operator +(Money a, Money b)
        => new Money(a.Cents + b.Cents);

    public static implicit operator Money(int c) => new Money(c);

    public static explicit operator int(Money m) => m.Cents;
}

class Program
{
    static void Main()
    {
        Money a = 250;              // implicit int -> Money
        Money b = a + 199;
        Console.WriteLine((int)b);  // explicit Money -> int
    }
}
