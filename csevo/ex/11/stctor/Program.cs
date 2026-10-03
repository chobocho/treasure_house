// 슬라이드 p11-v10-structctor — 구조체의 매개변수 없는 생성자, C# 10.0
using System;

struct Money
{
    public decimal Amount;
    public string Currency;

    public Money()                          // C# 10
    {
        Amount = 0;
        Currency = "KRW";
    }
}

class App
{
    static void Main()
    {
        Money m = new Money();
        Console.WriteLine(m.Amount + " " + m.Currency);
    }
}
