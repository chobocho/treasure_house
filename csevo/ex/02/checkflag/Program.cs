// 슬라이드 p2-v1-checkflag — 기본 넘침 문맥과 -checked 옵션, C# 1.0
using System;

class App
{
    static void Main()
    {
        int x = int.MaxValue;
        int y = unchecked(x + 1);                       // always wraps
        Console.WriteLine("unchecked: " + y);
        x++;                                            // depends
        Console.WriteLine("default:   " + x);
    }
}
