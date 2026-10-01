// 슬라이드 p4-v3-lambda-rec — 선언과 동시에 자신을 부르면, C# 3.0
using System;

class App
{
    static void Main()
    {
        Func<int, int> fact = n => n <= 1 ? 1 : n * fact(n - 1);
        Console.WriteLine(fact(5));
    }
}
