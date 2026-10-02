// 슬라이드 p8-v7_1-genericpat — 형식 매개변수 값에 형식 패턴, C# 7.1
using System;

class App
{
    static string Describe<T>(T value)
    {
        switch (value)                     // the input is a T
        {
            case int i: return "int " + (i + 1);
            case string s: return "string of " + s.Length;
#if BAD
            case null: return "null " + typeof(T).Name;
#endif
            default: return "other " + typeof(T).Name;
        }
    }

    static bool TryAs<T>(object o, out T result)
    {
        if (o is T t) { result = t; return true; }  // the type is a T
        result = default(T);
        return false;
    }

    static void Main()
    {
        Console.WriteLine(Describe(41));
        Console.WriteLine(Describe("abc"));
        Console.WriteLine(Describe<string>(null));
        Console.WriteLine(Describe(2.5));
        int n;
        Console.WriteLine(TryAs("x", out n) + " " + TryAs(7, out n) +
            " " + n);
    }
}
