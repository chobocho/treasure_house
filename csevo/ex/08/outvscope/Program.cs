// 슬라이드 p8-v7-outv-scope — out 변수의 범위와 확정 대입, C# 7.0
using System;

class App
{
    static void Main()
    {
        if (!int.TryParse("x", out var n))
            Console.WriteLine("failed, n = " + n);  // assigned anyway
        n += 10;                                 // still in scope here
        Console.WriteLine(n);

        int.TryParse("5", out var m);            // a statement
        Console.WriteLine(m * 2);                // m leaks as well

        var inputs = new[] { "1", "x", "3" };
        int sum = 0;
        for (int i = 0; i < inputs.Length; i++)
            if (int.TryParse(inputs[i], out var v))
                sum += v;                        // v: one per iteration
        Console.WriteLine(sum);
    }
}
