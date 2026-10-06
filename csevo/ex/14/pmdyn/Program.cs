// 슬라이드 p14-v13-pm-dyn — dynamic 과 params 컬렉션, C# 13
using System;
using System.Collections.Generic;

class Program
{
    public int A(params int[] xs) => xs.Length;
    public int L(params List<int> xs) => xs.Count;

    static void Main()
    {
        var p = new Program();
        dynamic d = 1;
        Console.WriteLine("A(d, d)    " + p.A(d, d));
#if BAD
        Console.WriteLine("L(d, d)    " + p.L(d, d));
#endif
        dynamic dp = p;
        Console.WriteLine("dp.A(1, 2) " + dp.A(1, 2));
        try
        {
            Console.WriteLine("dp.L(1, 2) " + dp.L(1, 2));
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
    }
}
