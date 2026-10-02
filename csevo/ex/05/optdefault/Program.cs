// 슬라이드 p5-v4-opt-default — 뒤 버전: 기본값에 default 리터럴, C# 7.1
using System;

struct Money
{
    public decimal Amount;
    public Money(decimal a) { Amount = a; }
}

class Program
{
    static void M(int n = default, string s = default,
                  Money m = default, int? x = default)
    {
        Console.WriteLine(n + " " + (s == null) + " " + m.Amount + " "
                          + x.HasValue);
    }

    static void Main()
    {
        M();
    }
}
