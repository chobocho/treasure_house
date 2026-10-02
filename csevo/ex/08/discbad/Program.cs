// 슬라이드 p8-v7-discard-bad — 버린 값은 읽을 수 없다, C# 7.0
using System;

class App
{
    static void Main()
    {
        var (_, b) = (1, 2);
        Console.WriteLine(_);           // read a discard
        _ = 5;
        int c = _ + 1;                  // still nothing to read
        _ = Console.WriteLine;          // no type to infer
    }
}
