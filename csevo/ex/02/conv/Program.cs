// 슬라이드 p2-v1-conv — 사용자 정의 변환 implicit·explicit, C# 1.0
using System;

struct Celsius
{
    double deg;
    public Celsius(double d) { deg = d; }

    // widening: never fails, never loses information
    public static implicit operator double(Celsius c) { return c.deg; }

    // narrowing: may throw, so the caller must write a cast
    public static explicit operator Celsius(double d)
    {
        if (d < -273.15) throw new ArgumentOutOfRangeException("d");
        return new Celsius(d);
    }
}

class App
{
    static void Main()
    {
        Celsius body = (Celsius)36.5;         // explicit: cast needed
        double d = body;                      // implicit: no cast
        Console.WriteLine(d + 1);
        Console.WriteLine(Math.Max(body, 40.0));
        Celsius cold = (Celsius)(-300.0);
        Console.WriteLine((double)cold);
    }
}
