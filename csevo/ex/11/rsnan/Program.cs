// 슬라이드 p11-v10-rs-nan — NaN 을 담은 record struct 의 같음, C# 10.0
using System;

record struct Reading(double Value);

class App
{
    static void Main()
    {
        var a = new Reading(double.NaN);
        var b = new Reading(double.NaN);
        Console.WriteLine("record ==   " + (a == b));
        Console.WriteLine("Equals      " + a.Equals(b));
        Console.WriteLine("double ==   " + (a.Value == b.Value));
        var t1 = (Value: double.NaN, 0);
        var t2 = (Value: double.NaN, 0);
        Console.WriteLine("tuple ==    " + (t1 == t2));
        Console.WriteLine("tuple Eq    " + t1.Equals(t2));
    }
}
