// 슬라이드 p8-v7-throw-where — throw 식을 못 쓰는 자리(의미), C# 7.0
using System;

class App
{
    static void Main(string[] args)
    {
        int a = throw new Exception();            // plain initializer
        Console.WriteLine(throw new Exception()); // an argument
        var d = args.Length > 0 ? throw new Exception()
                                : throw new Exception();
        var e = throw new Exception();            // no type at all
        string s = args.Length > 0 ? args[0]
                                   : (throw new Exception());
    }
}
