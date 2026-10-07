// 슬라이드 p15-v14-ca-incr — 인스턴스 ++ 와 결과를 쓰는 x++, C# 14
using System;

class Counter
{
    public int N;
    public static Counter operator ++(Counter c)
    {
        Console.Write("[static ++] ");
        return new Counter { N = c.N + 1 };
    }
    public void operator ++()
    {
        Console.Write("[instance ++] ");
        N++;
    }
}

class Program
{
    static void Main()
    {
        var c = new Counter();
        var c0 = c;
        c++;          Console.WriteLine("c++;      " + c.N);
        ++c;          Console.WriteLine("++c;      " + c.N);
        var a = ++c;  Console.WriteLine("a = ++c;  " + a.N);
        var b = c++;  Console.WriteLine("b = c++;  " + b.N + " " + c.N);
        Console.WriteLine("c is still c0: " + ReferenceEquals(c, c0));
    }
}
