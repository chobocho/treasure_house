// 슬라이드 p4-v3-lambda-closure — 잡는 것은 값이 아니라 변수, C# 3.0
using System;

class App
{
    static Func<int> MakeCounter()
    {
        int count = 0;
        return () => ++count;            // count outlives MakeCounter
    }

    static void Main()
    {
        Func<int> a = MakeCounter();
        Func<int> b = MakeCounter();
        Console.WriteLine(a() + " " + a() + " " + a() + " | " + b());

        int factor = 2;
        Func<int, int> scale = x => x * factor;
        factor = 10;             // changed after the lambda was made
        Console.WriteLine(scale(3));
    }
}
