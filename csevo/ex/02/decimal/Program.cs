// 슬라이드 p2-v1-decimal — 10진 실수 decimal, C# 1.0
using System;

class App
{
    static void Main()
    {
        double d = 0.1 + 0.2;
        decimal m = 0.1m + 0.2m;
        Console.WriteLine("double  " + d + " == 0.3? " + (d == 0.3));
        Console.WriteLine("decimal " + m + " == 0.3? " + (m == 0.3m));
        Console.WriteLine(1m / 3m);
        Console.WriteLine(1.0 / 3.0);
        Console.WriteLine(1.50m + " " + 1.5m.Equals(1.50m));
        Console.WriteLine(decimal.MaxValue);
        Console.WriteLine(sizeof(decimal) + " " + sizeof(double));

        double zero = 0;
        decimal mzero = 0;
        Console.WriteLine(1.0 / zero);
        Console.WriteLine(1m / mzero);
    }
}
