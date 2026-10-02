// 슬라이드 p10-v9-pat-paren — 괄호 패턴, C# 9.0
using System;

class App
{
    static bool A(int x) => x is not 0 and > -5;     // (not 0) and > -5
    static bool B(int x) => x is not (0 or > -5);    // not (0 or > -5)
    static bool C(int x) => x is (>= 1 and <= 3) or (>= 7 and <= 9);

    static void Main()
    {
        foreach (int x in new[] { -9, -1, 0, 2, 8 })
            Console.WriteLine($"{x}: {A(x)} {B(x)} {C(x)}");
    }
}
