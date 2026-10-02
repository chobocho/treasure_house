// 슬라이드 p10-v9-nint-ptr — IntPtr 에도 산술 연산자가, C# 9.0
using System;

class App
{
    static void Main()
    {
        IntPtr p = (IntPtr)8;
        IntPtr q = p * 3 + 1;
        Console.WriteLine(q + " " + (p < q) + " " + (q % 4));
    }
}
