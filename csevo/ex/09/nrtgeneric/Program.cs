// 슬라이드 p9-v8-nrt-generic — 제약 없는 T 는 둘 다일 수 있다, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static T First<T>(List<T> xs)
    {
        if (xs.Count == 0) return default;     // CS8603
        return xs[0];
    }

    static T Make<T>()
    {
        T t = default;                         // 8.0: no warning here
        return t;                              // CS8603
    }

    static string Show<T>(T t) => t.ToString();   // CS8602, CS8603

    static void Main()
    {
        Console.WriteLine(First(new List<string>()) == null);
        Console.WriteLine(Make<int>() + Show(1));
    }
}
