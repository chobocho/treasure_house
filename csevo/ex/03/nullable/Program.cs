// 슬라이드 p3-v2-nullable-gate — nullable 값 형식, C# 2.0
using System;

class App
{
    static int? Age(string s)
    {
        if (s.Length == 0) return null;   // "no value", no magic number
        return int.Parse(s);
    }

    static void Main()
    {
        int? a = Age("12");
        int? b = Age("");
        Console.WriteLine(a.HasValue + " " + a.Value);
        Console.WriteLine(b.HasValue);
        Console.WriteLine(b == null);
    }
}
