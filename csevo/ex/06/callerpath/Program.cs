// 슬라이드 p6-v5-caller-path — 파일 경로와 #line, C# 5.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Where(string tag,
        [CallerFilePath] string path = "",
        [CallerLineNumber] int line = 0)
    {
        Console.WriteLine(tag + ": " + path + ":" + line);
    }

    static string Path([CallerFilePath] string p = "")
    {
        return p;
    }

    static void Main()
    {
        Where("plain");
        // The string really is "/work/...": csrun's -pathmap.
        Console.WriteLine(Path() == "/work/Program.cs");
#line 500 "gen.cs"
        Where("after #line");
#line default
        Where("default");
    }
}
