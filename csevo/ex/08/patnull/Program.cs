// 슬라이드 p8-v7-pat-null — null 과 형식 패턴, C# 7.0
using System;

class App
{
    static string M(object o)
    {
        switch (o)
        {
            case string s: return "string";
            case object x: return "object";   // still not null
            default: return "default";
        }
    }

    static void Main()
    {
        string s = null;
        Console.WriteLine(s is string);       // static type string, but
        Console.WriteLine(M(s));              // null matches no type
        Console.WriteLine(M(""));
        object o = s;
        Console.WriteLine(o is string t ? "matched" : "no match");
    }
}
