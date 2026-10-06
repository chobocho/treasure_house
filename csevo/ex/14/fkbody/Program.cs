// 슬라이드 p14-v13-fk-ident — 몸체만 있는 접근자의 field, C# 14
using System;

class Temp
{
    public int Celsius
    {
        get { return field; }
        set { field = Math.Clamp(value, -273, 1000); }
    }
}

class Program
{
    static void Main()
    {
        var t = new Temp();
        t.Celsius = -500;
        Console.WriteLine(t.Celsius);
    }
}
