// 슬라이드 p15-v14-ca-fall — 없으면 x = x + y, 둘이 달라도 그만, C# 14
using System;

class OnlyPlus
{
    public int N;
    public static OnlyPlus operator +(OnlyPlus a, int d) =>
        new OnlyPlus { N = a.N + d };
}

class Odd                                  // + and += disagree
{
    public int N;
    public static Odd operator +(Odd a, int d) =>
        new Odd { N = a.N + d };
    public void operator +=(int d) => N -= d;
}

class Program
{
    static void Main()
    {
        var p = new OnlyPlus();
        var p0 = p;
        p += 5;
        Console.WriteLine("OnlyPlus: " + p.N + " new object: "
            + !ReferenceEquals(p, p0));

        var o = new Odd { N = 10 };
        o += 3;
        Console.WriteLine("Odd: o += 3 -> " + o.N);
        o = o + 3;
        Console.WriteLine("Odd: o = o + 3 -> " + o.N);
    }
}
