// 슬라이드 p7-v6-nullcond-nrt8 — nullable 참조 형식과 ?., C# 8.0
using System;

class App
{
    static int Len(string? s)
    {
        if (s?.Length > 0)
            return s.Length;          // no warning: s is not null here
        return s.Length;              // CS8602: s may be null
    }

    static void Main()
    {
        Console.WriteLine(Len("abc"));
        try { Console.WriteLine(Len(null)); }
        catch (NullReferenceException)
        { Console.WriteLine("NullReferenceException"); }
    }
}
