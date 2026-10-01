// 슬라이드 p3-v2-coalesce — ?? 연산자, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? a = null;
        int? b = 5;
        int x = a ?? -1;                  // int? ?? int  -> int
        int? y = a ?? b;                  // int? ?? int? -> int?
        Console.WriteLine(x + " " + y);
        Console.WriteLine(a ?? b ?? 0);   // right-associative
        string s = null;
        Console.WriteLine(s ?? "(none)"); // reference types too
    }
}
