// 슬라이드 p2-v1-simple — 단순 형식은 구조체의 별명, C# 1.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(typeof(int) == typeof(Int32));
        Console.WriteLine(typeof(int).FullName);
        Console.WriteLine(typeof(string).FullName);
        Console.WriteLine(typeof(decimal).IsValueType);
        Console.WriteLine(typeof(string).IsValueType);
        Console.WriteLine(42.GetType().Name + " " + 255.ToString("X"));
        Console.WriteLine(int.MaxValue + " " + long.MinValue);
        Console.WriteLine((int)'A' + " " + (char)66);
        Int32 n = 7;             // same type as int
        int m = n;
        Console.WriteLine(m.CompareTo(8));
    }
}
