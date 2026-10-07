// 슬라이드 p15-v14-compound — 사용자 정의 복합 대입 연산자, C# 14
using System;

class Vec
{
    public static int Made;
    public readonly double[] Data;
    public Vec(int n) { Data = new double[n]; Made++; }

    public static Vec operator +(Vec a, double d)
    {
        var r = new Vec(a.Data.Length);
        for (int i = 0; i < r.Data.Length; i++)
            r.Data[i] = a.Data[i] + d;
        return r;
    }

    public void operator +=(double d)      // instance, void, one param
    {
        for (int i = 0; i < Data.Length; i++) Data[i] += d;
    }
}

class Program
{
    static void Main()
    {
        var v = new Vec(1000);
        var first = v;
        for (int i = 0; i < 5; i++) v += 1;
        Console.WriteLine("Vec objects made: " + Vec.Made);
        Console.WriteLine("same object: " + ReferenceEquals(v, first));
        Console.WriteLine("v[0] = " + v.Data[0]);
        var w = v + 1;                     // binary + still allocates
        Console.WriteLine("after v + 1: " + Vec.Made);
    }
}
