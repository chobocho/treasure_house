// 슬라이드 p9-v8-co-err — ??= 가 안 되는 곳, C# 8.0
using System;

class App
{
    static void Main()
    {
        int n = 0;
        n ??= 1;                    // int can never be null
        Console.WriteLine(n);
#if AND
        bool a = true, b = false;
        a &&= b;                    // there is no &&= in C#
#endif
    }
}
