// 슬라이드 p10-v9-pat-reltype — 관계 패턴의 입력 형식, C# 9.0
using System;

class App
{
    static bool Pct(object x) => x is >= 0 and <= 100;

    static void Main()
    {
        char c = 'q';
        double d = 0.5;
        decimal m = 9.99m;
        int? n = null;
        Console.WriteLine((c is >= 'a') + " " + (d is > 0.0 and < 1.0)
            + " " + (m is < 10m) + " " + (n is > 0));
        Console.WriteLine("int 50   : " + Pct(50));
        Console.WriteLine("long 50  : " + Pct(50L));
        Console.WriteLine("double 50: " + Pct(50.0));
        Console.WriteLine("string   : " + Pct("50"));
#if NAN
        Console.WriteLine(d is < double.NaN);
#endif
#if VAR
        int limit = 10;
        Console.WriteLine(d is < limit);
#endif
    }
}
