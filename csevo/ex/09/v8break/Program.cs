// 슬라이드 p9-sum-break — C# 8 컴파일러가 새로 내는 경고, C# 8.0
using System;

class _ { }                                 // a type named _

class Flags
{
    const int _ = 0;                        // a constant named _

    public static string Name(int v)
    {
        switch (v)
        {
            case _: return "zero";      // the constant, not a discard
            default: return "other";
        }
    }
}

class App
{
    static void Main()
    {
        object o = new _();
        Console.WriteLine(o is _);          // the type, not a discard
        Console.WriteLine(3 is 4);          // a constant never matches
        Console.WriteLine(Flags.Name(0) + " " + Flags.Name(1));
    }
}
