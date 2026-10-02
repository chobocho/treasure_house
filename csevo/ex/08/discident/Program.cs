// 슬라이드 p8-v7-discard-ident — _ 라는 진짜 변수가 있으면, C# 7.0
using System;

class App
{
    static void NoLocal()
    {
        int.TryParse("1", out _);               // a discard
        Console.WriteLine("discarded");
    }

    static void WithLocal()
    {
#if BAD
        int.TryParse("1", out _);               // before the local
#endif
        int _ = 100;                            // an ordinary local
        Console.WriteLine(_);
        int.TryParse("7", out _);               // writes the local!
        Console.WriteLine(_);
        _ = 8;                                  // assigns the local
        Console.WriteLine(_ + 1);
        var (a, _) = (1, 2);                    // var (...): a discard
        Console.WriteLine(_ + a);
    }

    static void Main()
    {
        NoLocal();
        WithLocal();
    }
}
