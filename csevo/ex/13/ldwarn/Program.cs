// 슬라이드 p13-v12-ld-warn — 대리자와 기본값이 어긋나면, C# 12
using System;

delegate int NoDefault(int x);
delegate int WithDefault(int x = 1);
delegate int NoParams(int[] xs);

class Program
{
    static int MethodWithDefault(int x = 2) => x;

    static void Main()
    {
        NoDefault d1 = MethodWithDefault;      // method group: silent
        WithDefault d2 = MethodWithDefault;
        WithDefault d6 = (int x) => x;         // source has none: fine
        Console.WriteLine(d2() + " " + d6() + " " + d1(7));
#if WARN1
        NoDefault d4 = (int x = 1) => x;       // target has none
#endif
#if WARN2
        WithDefault d5 = (int x = 2) => x;     // 2 is never used
        Console.WriteLine(d5());
#endif
#if WARN3
        NoParams d9 = (params int[] xs) => xs.Length;
#endif
    }
}
