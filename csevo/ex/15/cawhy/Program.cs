// 슬라이드 p15-v14-ca-why — x += y 는 x = x + y 였다, C# 14
using System;

class Vec
{
    public static int Made;
    public readonly double[] Data;
    public Vec(int n) { Data = new double[n]; Made++; }

    // the only way before C# 14: build a new Vec
    public static Vec operator +(Vec a, double d)
    {
        var r = new Vec(a.Data.Length);
        for (int i = 0; i < r.Data.Length; i++)
            r.Data[i] = a.Data[i] + d;
        return r;
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
    }
}
