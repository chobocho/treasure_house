// 슬라이드 p9-v8-nrt-guard — 공개 API 의 null 검사는 남긴다, C# 8.0
#nullable enable
using System;

public static class Lib
{
    public static int Len(string s)
    {
        if (s is null) throw new ArgumentNullException(nameof(s));
        return s.Length;
    }

    public static int Len2(string s)
    {
        ArgumentNullException.ThrowIfNull(s);   // .NET 10 helper
        return s.Length;
    }
}

#nullable disable
class App
{
    static void Show(Exception e) => Console.WriteLine(e.Message);

    static void Main()
    {
        string none = null;                 // an old caller
        try { Lib.Len(none); }
        catch (ArgumentNullException e) { Show(e); }
        try { Lib.Len2(none); }
        catch (ArgumentNullException e) { Show(e); }
    }
}
