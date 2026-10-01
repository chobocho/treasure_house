// 슬라이드 p2-v1-implicitnum — 정밀도를 잃는 암시적 변환, C# 1.0
using System;

class App
{
    static void Main()
    {
        int big = 16777217;                   // 2^24 + 1
        float f = big;                        // implicit, no warning
        Console.WriteLine(big + " -> " + f.ToString("R") + " -> "
            + (int)f);

        long huge = 9007199254740993;         // 2^53 + 1
        double d = huge;                      // implicit, too
        Console.WriteLine(huge + " -> " + (long)d);

        int small = 7;
        long wide = small;                    // exact
        double exact = small;                 // exact
        Console.WriteLine(wide + " " + exact);
        decimal m = big;                      // int -> decimal: exact
        Console.WriteLine(m);
    }
}
