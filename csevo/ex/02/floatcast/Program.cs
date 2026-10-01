// 슬라이드 p2-v1-floatcast — 캐스트와 Convert 의 차이, C# 1.0
using System;

class App
{
    static void Main()
    {
        double[] xs = { 2.5, 3.5, -2.5, 2.7, -2.7 };
        foreach (double x in xs)
        {
            Console.WriteLine(x.ToString("0.0").PadLeft(5)
                + "  (int)=" + ((int)x).ToString().PadLeft(2)
                + "  Convert="
                + Convert.ToInt32(x).ToString().PadLeft(2)
                + "  Round=" + Math.Round(x).ToString().PadLeft(2));
        }
        Console.WriteLine((long)1e18 + " " + (float)0.1);
        decimal m = 2.5m;
        Console.WriteLine((int)m + " " + Decimal.Round(m));
    }
}
