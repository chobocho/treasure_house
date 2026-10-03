// 슬라이드 p11-v10-constinterp — 상수 보간 문자열, C# 10.0
using System;

class App
{
    const string Name = "csevo";
    const string Ver = "10";
    const string Title = $"{Name} v{Ver}";
    const string Path = $@"C:\{Name}\{nameof(App)}";
    const string Nest = $"<{$"[{Name}]"}>";
#if BAD
    const string Num = $"{42}";
    const string Pad = $"{Name,8}";
    const string Fmt = $"{Name:U}";
#endif

    static string Kind(string s) => s switch
    {
        Title => "title",
        $"{Name}!" => "shout",
        _ => "other",
    };

    static void Main()
    {
        Console.WriteLine(Title);
        Console.WriteLine(Path);
        Console.WriteLine(Nest);
        Console.WriteLine(Kind("csevo!"));
        Console.WriteLine(ReferenceEquals(Title, "csevo v10"));
    }
}
