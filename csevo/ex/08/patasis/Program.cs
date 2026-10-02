// 슬라이드 p8-v7-pat-asis — as 와 null 검사를 한 식으로, C# 7.0
using System;

class App
{
    static string Old(object o)
    {
        var s = o as string;                // C# 6: two steps
        if (s != null) return "string of " + s.Length;
        if (o is int)                       // value types: is + cast
            return "int " + ((int)o + 1);
        return "other";
    }

    static string New(object o)
    {
        if (o is string s) return "string of " + s.Length;
        if (o is int i) return "int " + (i + 1);    // no cast
        return "other";
    }

    static void Main()
    {
        foreach (object o in new object[] { "abc", 41, null })
            Console.WriteLine(Old(o) + " | " + New(o));
    }
}
