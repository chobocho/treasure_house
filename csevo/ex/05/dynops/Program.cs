// 슬라이드 p5-v4-dyn-ops — 연산자도 실행 중에 고른다, C# 4.0
using System;

class Money
{
    public decimal Amount;
    public Money(decimal a) { Amount = a; }
    public static Money operator +(Money x, Money y)
    {
        return new Money(x.Amount + y.Amount);
    }
    public override string ToString() { return Amount + " won"; }
}

class Program
{
    static void Show(dynamic r)
    {
        Console.WriteLine("{0,-10} {1}", r, r.GetType().Name);
    }

    static void Main()
    {
        dynamic a = 7, b = 2;
        Show(a / b);
        a = 7.0;
        Show(a / b);
        a = "7";
        Show(a + b);
        dynamic x = (byte)1, y = (byte)2;
        Show(x + y);
        dynamic m = new Money(500m);
        Show(m + new Money(250m));
    }
}
