// 슬라이드 p8-v7-outv-overload — out var 와 오버로드, C# 7.0
using System;

class App
{
    static void Get(out int x) { x = 1; }
    static void Get(out string x) { x = "one"; }

    static void Main()
    {
        Get(out int i);                 // the type picks the overload
        Get(out string s);
        Console.WriteLine(i + " " + s);
#if BAD
        Get(out var v);                 // no type: ambiguous
#endif
    }
}
