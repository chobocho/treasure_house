// 슬라이드 p9-v8-nrt-lambda — 람다가 포착한 변수의 상태, C# 8.0
#nullable enable
using System;

class App
{
    static void Main()
    {
        string? s = "abc";
        Action show = () => Console.WriteLine(s.Length);  // no warning
        s = null;
        Func<int> len = () => s.Length;                    // CS8602
        Console.WriteLine("calling show()");
        show();
    }
}
