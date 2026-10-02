// 슬라이드 p10-v9-pat-type — 형식 패턴, C# 9.0
using System;

class App
{
    static string Kind(object o) => o switch
    {
        int => "int",
        long or short => "other integer",
        string => "string",
        null => "null",
        _ => o.GetType().Name,
    };

    static void Main()
    {
        foreach (object o in new object[] { 1, 2L, "s", null, 1.5 })
            Console.WriteLine(Kind(o));
        (object, object) t = (1, "x");
        Console.WriteLine(t is (int, string));
    }
}
