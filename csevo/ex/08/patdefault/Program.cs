// 슬라이드 p8-v7-pat-default — default 는 어디에 있든 마지막, C# 7.0
using System;

class App
{
    static string M(object o)
    {
        switch (o)
        {
            default:                        // written first ...
                return "default";
            case int n when n > 0:
                return "positive int";
            case null:                      // ... still checked last
                return "null";
        }
    }

    static void Main()
    {
        Console.WriteLine(M(5));
        Console.WriteLine(M(-5));
        Console.WriteLine(M(null));
        Console.WriteLine(M("x"));
    }
}
