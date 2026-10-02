// 슬라이드 p8-v7_1-genericpat-before — C# 7.0 의 T 검사, C# 7.0
using System;

class App
{
    static string Describe<T>(T value)
    {
        object o = value;                  // box once, then test
        if (o is int i) return "int " + (i + 1);
        if (o is string s) return "string of " + s.Length;
        return "other " + typeof(T).Name;
    }

    static string Cast<T>(T value)
    {
        if (value is int)                  // 'is' without a pattern
            return "int " + ((int)(object)value + 1);
        return "other";
    }

    static void Main()
    {
        Console.WriteLine(Describe(41) + " / " + Describe("abc"));
        Console.WriteLine(Cast(41) + " / " + Cast(2.5));
    }
}
