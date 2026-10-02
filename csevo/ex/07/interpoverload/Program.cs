// 슬라이드 p7-v6-interp-overload — 오버로드 고르기, C# 6.0
using System;

class Both
{
    public static void M(string s) { Console.WriteLine("string"); }
    public static void M(FormattableString f)
    { Console.WriteLine("FormattableString"); }
}

class OnlyF
{
    public static void M(FormattableString f)
    { Console.WriteLine("FormattableString: " + f.Format); }
}

class FAndI
{
    public static void M(IFormattable f)
    { Console.WriteLine("IFormattable"); }
    public static void M(FormattableString f)
    { Console.WriteLine("FormattableString"); }
}

class App
{
    static void Main()
    {
        int id = 7;
        Both.M($"id={id}");                      // string wins
        Both.M((FormattableString)$"id={id}");   // only by cast
        OnlyF.M($"id={id}");
        FAndI.M($"id={id}");
#if BAD
        string s = $"id={id}";
        OnlyF.M(s);              // a string is no longer a format
#endif
    }
}
