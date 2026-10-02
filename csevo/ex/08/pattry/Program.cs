// 슬라이드 p8-v7-pat-try — 패턴과 Try 메서드, C# 7.0
using System;

class App
{
    static int? AsNumber(object o)
    {
        if (o is int i || (o is string s && int.TryParse(s, out i)))
            return i;                       // one i for both paths
        return null;
    }

    static void Main()
    {
        foreach (object o in new object[] { 7, "12", "x", 1.5 })
            Console.WriteLine((AsNumber(o)?.ToString() ?? "-"));
    }
}
