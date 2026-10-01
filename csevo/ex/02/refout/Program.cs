// 슬라이드 p2-v1-refout — ref 와 out 매개변수, C# 1.0
using System;

class App
{
    static void Swap(ref int a, ref int b)
    {
        int t = a; a = b; b = t;
    }

    static bool TryHalf(int n, out int half)
    {
        if (n % 2 != 0)
        {
            half = 0;                 // out: must assign on every path
            return false;
        }
        half = n / 2;
        return true;
    }

    static void Main()
    {
        int x = 1, y = 2;
        Swap(ref x, ref y);           // ref at the call site, too
        Console.WriteLine(x + " " + y);

        int h;                        // no need to initialise for out
        if (TryHalf(10, out h)) Console.WriteLine("half of 10 = " + h);
        Console.WriteLine(TryHalf(7, out h) + " " + h);
    }
}
