// 슬라이드 p13-v12-ex-opts — 진단 문장과 전파, C# 12.0
using System;
using System.Diagnostics.CodeAnalysis;

static class Lib
{
    [Experimental("MY002", UrlFormat = "https://example.org/{0}")]
    public static int Url(int x) => x;

    [Experimental("MY003", Message = "renamed to Fast2")]
    public static int Msg(int x) => x;
}

[Experimental("MY004")]
static class Wrapper
{
    // inside an experimental member: no diagnostic
    public static int Both() => Lib.Url(1) + Lib.Msg(2);
}

#if BAD
static class Bad
{
    [Experimental("MY 005")] public static void X() { }
}
#endif

class App
{
    static void Main()
    {
#if U1
        Console.WriteLine(Lib.Url(1));
#elif U2
        Console.WriteLine(Lib.Msg(1));
#elif U3
        Console.WriteLine(Wrapper.Both());   // MY004 here
#endif
        Console.WriteLine("built");
    }
}
