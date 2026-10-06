// 슬라이드 p13-v12-ld-dpv — [DefaultParameterValue] 를 람다에, C# 12
using System;
using System.Runtime.InteropServices;

class Program
{
    static void Main()
    {
        var a = (int i = 13) => i;
        var b = ([Optional, DefaultParameterValue(13)] int i) => i;
        Console.WriteLine(a() + " " + b() + " " + b(5));
        Console.WriteLine(a.GetType() == b.GetType());
        b = a;                              // same synthesized type
        var p = b.GetType().GetMethod("Invoke").GetParameters()[0];
        Console.WriteLine(p.IsOptional + " " + p.DefaultValue);
    }
}
