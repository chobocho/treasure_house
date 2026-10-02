// 슬라이드 p8-v7-pat-var — var 패턴은 null 에도 맞는다, C# 7.0
using System;

class App
{
    static string Upper() => null;

    static void Main()
    {
        object o = null;
        Console.WriteLine(o is object);         // type test: false
        Console.WriteLine(o is var x);          // var: always true
        Console.WriteLine(x == null);

        // var pattern names a sub-expression inside a condition
        if (Upper() is var u && u != null)
            Console.WriteLine(u.Length);
        else
            Console.WriteLine("u is null");

        switch (o)
        {
            case string s: Console.WriteLine("string"); break;
            case var other:
                Console.WriteLine("var: " + (other ?? "null"));
                break;
        }
    }
}
