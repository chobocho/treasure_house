// 슬라이드 p2-v1-opcompound — += 은 새 객체를 만든다, C# 1.0
using System;

class Total
{
    public int Sum;
    public Total(int s) { Sum = s; }

    public static Total operator +(Total t, int n)
    {
        Console.WriteLine("  op_Addition(" + t.Sum + ", " + n + ")");
        return new Total(t.Sum + n);          // a new object each time
    }
}

class App
{
    static void Main()
    {
        Total t = new Total(1);
        Total alias = t;
        t += 2;                               // t = t + 2
        Console.WriteLine("t.Sum=" + t.Sum + " alias.Sum=" + alias.Sum);
        Console.WriteLine("same object? " + (t == alias));
    }
}
