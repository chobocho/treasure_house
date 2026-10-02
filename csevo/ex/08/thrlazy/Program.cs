// 슬라이드 p8-v7-throw-lazy — 예외 객체는 그 가지에서만 만든다, C# 7.0
using System;

class App
{
    static Exception Make(string why)
    {
        Console.WriteLine("  Make(" + why + ")");
        return new ArgumentException(why);
    }

    static string Check(string s) => s ?? throw Make("null");

    static void Main()
    {
        Console.WriteLine(Check("x"));        // Make is not called
        try { Check(null); }
        catch (ArgumentException e) { Console.WriteLine(e.Message); }

        string t = null;
        try { Console.WriteLine(t ?? throw null); }
        catch (NullReferenceException)
        {
            Console.WriteLine("throw null -> NullReferenceException");
        }
    }
}
