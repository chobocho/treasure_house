// 슬라이드 p2-v1-unbox — 언박싱은 정확히 그 형식으로만, C# 1.0
using System;

class App
{
    static void Main()
    {
        object o = 42;                 // a boxed int
        long a = (int)o;               // unbox to int, then widen
        Console.WriteLine("a = " + a);
        Console.WriteLine("o is int:  " + (o is int));
        Console.WriteLine("o is long: " + (o is long));
        long b = (long)o;              // unbox to long: wrong type
        Console.WriteLine("b = " + b);
    }
}
