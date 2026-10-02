// 슬라이드 p9-v8-nrt-restore — #nullable restore, C# 8.0
using System;

class App
{
#nullable enable
    static string? Maybe() => null;       // always annotated here
#nullable restore
    // from here on: whatever the project (-nullable:) says
    static string Name() => null;

    static void Main()
    {
        Console.WriteLine(Maybe() ?? "null");
        Console.WriteLine(Name() ?? "null");
    }
}
