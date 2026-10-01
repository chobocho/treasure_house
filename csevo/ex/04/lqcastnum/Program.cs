// 슬라이드 p4-v3-linq-cast-trap — Cast<long>() 은 변환이 아니다, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        long direct = xs[0];                  // implicit int -> long
        Console.WriteLine(direct);
        try
        {
            long[] ls = xs.Cast<long>().ToArray();
            Console.WriteLine(ls.Length);
        }
        catch (InvalidCastException e)
        {
            Console.WriteLine(e.Message);
        }
        long[] ok = xs.Select(x => (long)x).ToArray();
        Console.WriteLine(string.Join(" ", ok));
    }
}
