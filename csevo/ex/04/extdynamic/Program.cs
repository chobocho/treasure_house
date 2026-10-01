// 슬라이드 p4-v3-ext-dynamic — dynamic 은 확장 메서드를 못 본다, C# 4
using System;

static class StringExt
{
    public static string Shout(this string s)
    {
        return s.ToUpper() + "!";
    }
}

class App
{
    static void Main()
    {
        dynamic d = "hello";
        Console.WriteLine(StringExt.Shout(d));   // ordinary static call
        Console.WriteLine(d.Shout());            // extension syntax
    }
}
