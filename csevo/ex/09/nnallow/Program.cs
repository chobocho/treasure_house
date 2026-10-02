// 슬라이드 p9-v8-nrt-allownull — AllowNull 과 DisallowNull, C# 8.0
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

class Profile
{
    string screenName = "guest";
    string? comment;

    // never returns null, but null may be set (meaning "reset")
    [AllowNull]
    public string ScreenName
    {
        get => screenName;
        set => screenName = value ?? "guest";
    }

    // may return null, but callers must not set null
    [DisallowNull]
    public string? Comment
    {
        get => comment;
        set => comment = value ?? throw new ArgumentNullException();
    }
}

class App
{
    static void Main()
    {
        var p = new Profile();
        p.ScreenName = "ada";
        p.ScreenName = null;                 // allowed: no warning
        Console.WriteLine(p.ScreenName.Length);
        Console.WriteLine(p.Comment?.Length ?? -1);
        p.Comment = "hi";
#if BAD
        p.Comment = null;                    // CS8625
#endif
        Console.WriteLine(p.Comment.Length); // not null after set
    }
}
