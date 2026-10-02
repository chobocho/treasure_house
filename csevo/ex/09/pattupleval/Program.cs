// 슬라이드 p9-v8-tuplepat-eval — 튜플 리터럴을 고를 때, C# 8.0
using System;

class App
{
    static int A() { Console.Write("A "); return 1; }
    static int B() { Console.Write("B "); return 2; }

    static void Main()
    {
        // each element is evaluated once, left to right
        string r = (A(), B()) switch
        {
            (0, _) => "first zero",
            (1, 1) => "one one",
            (1, var b) => "one and " + b,
            _ => "other",
        };
        Console.WriteLine(r);

        // switch statement: the extra parentheses are optional
        switch (A(), B())
        {
            case (1, 2):
                Console.WriteLine("case (1, 2)");
                break;
        }
    }
}
