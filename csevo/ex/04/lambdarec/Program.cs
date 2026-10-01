// 슬라이드 p4-v3-lambda-rec — 먼저 선언하고 나중에 담는다, C# 3.0
using System;

class App
{
    static void Main()
    {
        Func<int, int> fact = null;
        fact = n => n <= 1 ? 1 : n * fact(n - 1);
        Console.WriteLine(fact(5));

        Func<int, int> alias = fact;
        fact = n => -1;              // the lambda calls the variable…
        Console.WriteLine(alias(5));     // …so this now prints 5 * -1
    }
}
