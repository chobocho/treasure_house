// 슬라이드 p11-v10-st-default — 생성자가 도는 곳, C# 10.0
using System;

struct Money
{
    public string Currency;
    public Money() { Currency = "KRW"; }
    public override string ToString() => Currency ?? "(null)";
}

class Wallet { public Money Cash { get; set; } }

class App
{
    static T Make<T>() where T : new() => new T();

    static void Main()
    {
        Console.WriteLine("new Money()      " + new Money());
        Console.WriteLine("default(Money)   " + default(Money));
        Console.WriteLine("new Money[1][0]  " + (new Money[1])[0]);
        Console.WriteLine("field of a class " + new Wallet().Cash);
        Console.WriteLine("new T()          " + Make<Money>());
        Money local = default;
        Console.WriteLine("Money m = default " + local);
    }
}
