// 슬라이드 p8-v7-tuple-big — 일곱 개를 넘으면 Rest 로 잇는다, C# 7.0
using System;

class App
{
    static void Main()
    {
        var t = (1, 2, 3, 4, 5, 6, 7, 8, 9);
        Console.WriteLine(t);
        Console.WriteLine(t.Item9);             // source sees Item9
        Console.WriteLine(t.Rest);              // metadata has Rest
        Console.WriteLine(t.Rest.Item2);        // the same element

        Type ty = t.GetType();
        while (true)
        {
            Type[] args = ty.GetGenericArguments();
            Console.WriteLine(ty.Name + " args=" + args.Length);
            if (args.Length < 8) break;
            ty = args[7];                       // TRest
        }
        var big = (a: 1, b: 2, c: 3, d: 4, e: 5, f: 6, g: 7, h: 8);
        Console.WriteLine(big.h + " " + big.Rest);
    }
}
