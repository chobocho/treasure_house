// 슬라이드 p11-v10-rs-readonly — readonly record struct, C# 10.0
using System;
using System.Reflection;

readonly record struct Temp(double Celsius)
{
    public double Fahrenheit => Celsius * 9 / 5 + 32;
}

class App
{
    static void Main()
    {
        var t = new Temp(100);
        var u = t with { Celsius = 0 };     // new value, t unchanged
        Console.WriteLine(t + " " + u);
        var set = typeof(Temp).GetProperty("Celsius").SetMethod;
        Console.WriteLine(set.Name + " modreq "
            + set.ReturnParameter.GetRequiredCustomModifiers()[0].Name);
#if BAD
        t.Celsius = 50;
#endif
    }
}
