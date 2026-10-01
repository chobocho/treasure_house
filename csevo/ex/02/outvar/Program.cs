// 슬라이드 p2-v1-outvar — 호출 자리에서 out 변수 선언은 C# 7, C# 1.0
using System;

class App
{
    static bool TryHalf(int n, out int half)
    {
        half = n / 2;
        return n % 2 == 0;
    }

    static void Main()
    {
        int h;
        if (TryHalf(10, out h)) Console.WriteLine(h);    // C# 1
        if (TryHalf(8, out int h2)) Console.WriteLine(h2); // C# 7
    }
}
