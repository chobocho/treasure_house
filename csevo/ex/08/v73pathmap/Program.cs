// 슬라이드 p8-v7_3-options — -pathmap 이 바꾼 경로, C# 7.3
using System;
using System.Runtime.CompilerServices;

class App
{
    static string Where([CallerFilePath] string file = "",
                        [CallerLineNumber] int line = 0)
    {
        return file + ":" + line;
    }

    static void Main()
    {
        Console.WriteLine(Where());
    }
}
