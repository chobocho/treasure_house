// 슬라이드 p15-v14-ca-virt — virtual·override·인터페이스, C# 14
using System;

interface IAccum
{
    void operator +=(int d);               // abstract instance operator
}

class Sum : IAccum
{
    public int N;
    public virtual void operator +=(int d) => N += d;
}

class LoudSum : Sum
{
    public override void operator +=(int d)
    {
        Console.Write("[LoudSum] ");
        base.N += d;
    }
}

struct SSum : IAccum
{
    public int N;
    public void operator +=(int d) => N += d;
}

class Program
{
    static void AddAll<T>(ref T acc) where T : IAccum
    {
        for (int i = 1; i <= 3; i++) acc += i;
    }

    static void Main()
    {
        Sum s = new LoudSum();
        s += 1;
        Console.WriteLine(s.N);
        var t = new SSum();
        AddAll(ref t);
        var u = new Sum();
        AddAll(ref u);
        Console.WriteLine(t.N + " " + u.N);
    }
}
