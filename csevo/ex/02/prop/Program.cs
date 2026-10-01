// 슬라이드 p2-v1-prop — 속성은 필드처럼 쓰는 메서드, C# 1.0
using System;

class Thermostat
{
    double celsius;                         // backing field, by hand

    public double Celsius
    {
        get { return celsius; }
        set
        {
            if (value < -273.15)
                throw new ArgumentOutOfRangeException("value");
            celsius = value;                // 'value' is implicit
        }
    }

    public double Fahrenheit                // computed, no field
    {
        get { return celsius * 9 / 5 + 32; }
    }
}

class App
{
    static void Main()
    {
        Thermostat t = new Thermostat();
        t.Celsius = 25;
        t.Celsius += 5;                     // get, then set
        Console.WriteLine(t.Celsius + " C = " + t.Fahrenheit + " F");
        try { t.Celsius = -300; }
        catch (ArgumentOutOfRangeException e)
        {
            Console.WriteLine("rejected: " + e.ParamName);
        }
    }
}
