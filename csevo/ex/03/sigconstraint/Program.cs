// 슬라이드 p3-v2-sig-trap — 제약은 시그니처가 아니다, C# 2.0
using System;

class App
{
    static void M<T>(T x) where T : struct { Console.Write("S"); }
    static void M<T>(T x) where T : class { Console.Write("C"); }

    static void Main()
    {
        M(1);
        M("s");
    }
}
