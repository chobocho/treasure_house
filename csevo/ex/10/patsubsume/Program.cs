// 슬라이드 p10-v9-pat-subsume — 맞을 수 없는·이미 다룬 패턴, C# 9.0
using System;

class App
{
    static string F(int x)
    {
        switch (x)
        {
            case < 2: return "under 2";
#if DUP
            case 0 or 1: return "zero or one";
#endif
#if NEVER
            case > 5 and < 3: return "never";
#endif
#if REDUNDANT
            case 2 or 3 or 2: return "two or three";
#endif
            default: return "2 or more";
        }
    }

    static void Main() => Console.WriteLine(F(1) + ", " + F(2));
}
