// 슬라이드 p5-v4-dyn-check — 맞는 후보가 없으면 컴파일 오류, C# 4.0
using System;

class Program
{
    static void Main()
    {
        dynamic d = -5;
        Console.WriteLine(Math.Abs(d));
#if BAD
        Console.WriteLine(Math.Abs(d, d));
#endif
    }
}
