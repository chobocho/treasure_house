// 슬라이드 p8-v7-outv-gate — out 변수 선언, C# 7.0
using System;

class App
{
    static void Main()
    {
        string input = "42";

        int a;                                  // C# 6: declare first
        if (int.TryParse(input, out a))
            Console.WriteLine(a + 1);

        if (int.TryParse(input, out int b))     // C# 7.0: in place
            Console.WriteLine(b + 1);
    }
}
