// 슬라이드 p2-v1-nan — NaN 은 자기 자신과도 같지 않다, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        double zero = 0;
        double nan = zero / zero;
        double same = nan;
        Console.WriteLine("nan == nan     " + (nan == same));
        Console.WriteLine("nan != nan     " + (nan != same));
        Console.WriteLine("nan.Equals     " + nan.Equals(nan));
        Console.WriteLine("Double.IsNaN   " + Double.IsNaN(nan));
        Console.WriteLine("nan < 1, > 1   " + (nan < 1) + " "
            + (nan > 1));

        ArrayList list = new ArrayList();
        list.Add(nan);
        Console.WriteLine("IndexOf(nan)   " + list.IndexOf(nan));
        Console.WriteLine("0.0 == -0.0    " + (0.0 == -zero));
        Console.WriteLine("1/-0.0         " + (1 / -zero));
    }
}
