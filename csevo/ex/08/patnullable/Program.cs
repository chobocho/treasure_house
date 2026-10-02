// 슬라이드 p8-v7-pat-nullable — Nullable 과 형식 패턴, C# 7.0
using System;

class App
{
    static void Show(int? x)
    {
        if (x is int v)                 // matches when HasValue
            Console.WriteLine("int " + v);
        else
            Console.WriteLine("no value");
    }

    static void Main()
    {
        Show(3);
        Show(null);
        object boxed = (int?)4;         // boxes as a plain int
        Console.WriteLine(boxed is int);
        Console.WriteLine(boxed.GetType().Name);
#if BAD
        Console.WriteLine(boxed is int? w);
#endif
    }
}
