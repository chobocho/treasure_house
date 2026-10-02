// 슬라이드 p7-v6-eb-not6 — 생성자·종료자·접근자의 =>, C# 7.0
using System;

class Temp
{
    double c;

    public Temp(double c) => this.c = c;      // constructor
    ~Temp() => c = 0;                         // finalizer

    public double Celsius
    {
        get => c;                             // get accessor
        set => c = value;                     // set accessor
    }

    public double Fahrenheit => c * 9 / 5 + 32;   // C# 6 already
}

class Program
{
    static void Main()
    {
        Temp t = new Temp(100);
        t.Celsius = 37;
        Console.WriteLine(t.Celsius + " C = " + t.Fahrenheit + " F");
    }
}
