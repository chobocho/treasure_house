// 슬라이드 p7-v6-eb-lambda — 람다를 돌려주는 식 본문 속성, C# 6.0
using System;

class Calc
{
    int n = 10;

    public Func<int, int> Inc => x => x + 1;     // captures nothing
    public Func<int, int> AddN => x => x + n;    // captures this
}

class Program
{
    static void Main()
    {
        Calc c = new Calc();
        Console.WriteLine(c.Inc(1) + " " + c.AddN(1));
        Console.WriteLine(ReferenceEquals(c.Inc, c.Inc));
        Console.WriteLine(ReferenceEquals(c.AddN, c.AddN));
    }
}
