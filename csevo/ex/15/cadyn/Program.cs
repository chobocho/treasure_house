// 슬라이드 p15-v14-ca-dyn — dynamic 의 복합 대입, C# 14
using System;
using Microsoft.CSharp.RuntimeBinder;

class Vec
{
    public int N;
#if !NOSTATIC
    public static Vec operator +(Vec a, int d)
    {
        Console.Write("[static +] ");
        return new Vec { N = a.N + d };
    }
#endif
    public void operator +=(int d)
    {
        Console.Write("[instance +=] ");
        N += d;
    }
}

class Program
{
    static void Main()
    {
        Vec v = new Vec();
        v += 1;
        Console.WriteLine(v.N);
        dynamic d = new Vec();
        try
        {
            d += 1;
            Console.WriteLine(d.N);
        }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
