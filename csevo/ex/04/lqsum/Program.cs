// 슬라이드 p4-v3-linq-sum — 루프는 넘치고 Sum 은 던진다, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] big = { int.MaxValue, 1 };

        int loop = 0;
        foreach (int x in big)
        {
            loop += x;                  // unchecked by default
        }
        Console.WriteLine("loop: " + loop);

        try
        {
            Console.WriteLine("Sum: " + big.Sum());
        }
        catch (OverflowException e)
        {
            Console.WriteLine("Sum: " + e.GetType().Name);
        }
        Console.WriteLine("Sum as long: " + big.Sum(x => (long)x));
    }
}
