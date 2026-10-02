// 슬라이드 p9-v8-obsacc — 접근자 하나에만 [Obsolete], C# 8.0
using System;

class Temp
{
    double c;

    public double Celsius
    {
        get => c;                               // still fine to read
        [Obsolete("use Set")] set => c = value;
    }

    public void Set(double v) => c = v;
}

class App
{
    static void Main()
    {
        var t = new Temp();
        t.Set(20);
        Console.WriteLine(t.Celsius);
        t.Celsius = 25;                         // warning CS0618
        Console.WriteLine(t.Celsius);
    }
}
