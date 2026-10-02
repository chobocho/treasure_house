// 슬라이드 p10-v9-rec-eqnan — 레코드의 == 와 필드의 ==, C# 9.0
using System;

record Reading(double Value);

class App
{
    static void Main()
    {
        double nan = double.NaN, nan2 = double.NaN;
        Console.WriteLine("nan == nan2         " + (nan == nan2));
        Console.WriteLine("nan.Equals(nan2)    " + nan.Equals(nan2));
        Console.WriteLine("record ==           "
            + (new Reading(nan) == new Reading(nan)));
        Console.WriteLine("0.0 == -0.0         " + (0.0 == -0.0));
        Console.WriteLine("record 0.0 == -0.0  "
            + (new Reading(0.0) == new Reading(-0.0)));
        Console.WriteLine("same hash           "
            + (new Reading(0.0).GetHashCode()
               == new Reading(-0.0).GetHashCode()));
        var t1 = (nan, 1);
        var t2 = (nan2, 1);
        Console.WriteLine("tuple ==            " + (t1 == t2));
    }
}
