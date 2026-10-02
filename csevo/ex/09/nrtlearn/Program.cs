// 슬라이드 p9-v8-nrt-learn — 검사가 '어쩌면 null' 을 가르친다, C# 8.0
#nullable enable
using System;

class App
{
    static int Len(string s)              // declared non-nullable
    {
        if (s == null)
            Console.WriteLine("someone passed null anyway");
        return s.Length;                  // CS8602
    }

    static int Len2(string s)
    {
        Console.WriteLine(s == null ? "null" : "not null");
        return s.Length;                  // CS8602 again
    }

    static void Main()
    {
        Console.WriteLine(Len("abc") + Len2("de"));
    }
}
