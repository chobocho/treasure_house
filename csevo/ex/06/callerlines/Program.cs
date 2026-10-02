// 슬라이드 p6-v5-caller-lines — 줄 번호의 형식과 여러 줄 호출, C# 5.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static long AsLong([CallerLineNumber] long n = 0) { return n; }
    static double AsDbl([CallerLineNumber] double n = 0) { return n; }
    static object AsObject([CallerLineNumber] object n = null)
    {
        return n;
    }

    static int Line([CallerLineNumber] int n = 0) { return n; }

    static void Main()
    {
        object o = AsObject();
        Console.WriteLine(AsLong() + " " + AsDbl() + " "
            + o + " (" + o.GetType().Name + ")");
        Console.WriteLine("split call: " + Line(
            ));
        Console.WriteLine("nested:     " + Math.Max(0,
            Line()));
    }
}
