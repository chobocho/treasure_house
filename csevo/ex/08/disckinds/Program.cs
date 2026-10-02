// 슬라이드 p8-v7-discard-kinds — _ 를 쓸 수 있는 네 자리, C# 7.0
using System;

class App
{
    static (string, int, double) City() => ("Seoul", 9411, 605.2);

    static void Main()
    {
        var (_, pop, _) = City();               // 1 deconstruction
        Console.WriteLine(pop);

        if (int.TryParse("42", out _))          // 2 out argument
            Console.WriteLine("a number");

        object o = 3.5;
        if (o is double _)                      // 3 pattern
            Console.WriteLine("a double");
        switch (o)
        {
            case int _: Console.WriteLine("int"); break;
            case var _: Console.WriteLine("anything"); break;
        }

        _ = City();                             // 4 standalone
        (_, _, _) = City();                     // types differ: fine
    }
}
