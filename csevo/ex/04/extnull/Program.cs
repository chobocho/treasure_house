// 슬라이드 p4-v3-ext-null — null 수신자도 호출은 된다, C# 3.0
using System;

static class StringExt
{
    public static bool IsBlank(this string s)
    {
        return s == null || s.Trim().Length == 0;
    }

    public static int SafeLength(this string s)
    {
        if (s == null) throw new ArgumentNullException("s");
        return s.Length;
    }
}

class App
{
    static void Main()
    {
        string s = null;
        Console.WriteLine("IsBlank: " + s.IsBlank());
        try { Console.WriteLine(s.Length); }
        catch (NullReferenceException)
        {
            Console.WriteLine("s.Length: NullReferenceException");
        }
        try { Console.WriteLine(s.SafeLength()); }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("SafeLength: " + e.GetType().Name
                + " " + e.ParamName);
        }
    }
}
