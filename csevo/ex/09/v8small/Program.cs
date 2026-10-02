// 슬라이드 p9-v8-small — 작은 변화들, C# 8.0
using System;

class App
{
    // `is null` on an unconstrained type parameter
    static bool IsNull<T>(T t) => t is null;

    static void Main()
    {
        string dir = "tmp";
        Console.WriteLine(@$"C:\{dir}\a.txt");    // @ before $
        Console.WriteLine(IsNull<string>(null) + " " + IsNull(0)
            + " " + IsNull<int?>(null));
    }
}
