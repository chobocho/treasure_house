// 슬라이드 p2-v1-convtrap — 언박싱에는 사용자 변환이 없다, C# 1.0
using System;

struct Celsius
{
    double deg;
    public Celsius(double d) { deg = d; }
    public static implicit operator double(Celsius c) { return c.deg; }
}

class App
{
    static void Main()
    {
        Celsius c = new Celsius(36.5);
        double d1 = c;                        // user-defined: fine
        double d2 = (double)c;                // same, written
        Console.WriteLine(d1 + " " + d2);

        object o = c;                         // boxed Celsius
        Console.WriteLine(o is Celsius);
        Console.WriteLine(o is double);
        double d3 = (double)o;                // unboxing only
        Console.WriteLine(d3);
    }
}
