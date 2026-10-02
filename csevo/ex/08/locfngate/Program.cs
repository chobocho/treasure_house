// 슬라이드 p8-v7-locfn-gate — 지역 함수, C# 7.0
using System;

class App
{
    static int SumOfSquares(int[] xs)
    {
        int total = 0;
        foreach (int x in xs) total += Square(x);
        return total;

        int Square(int v) => v * v;     // visible only in this method
    }

    static void Main()
    {
        Console.WriteLine(SumOfSquares(new[] { 1, 2, 3 }));
    }
}
