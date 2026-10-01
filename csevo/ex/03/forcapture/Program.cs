// 슬라이드 p3-v2-for-capture — for 의 반복 변수를 잡으면, C# 2.0
using System;

delegate void D();

class App
{
    static void Main()
    {
        D[] ds = new D[3];
        for (int i = 0; i < 3; i++)
        {
            ds[i] = delegate { Console.Write(i + " "); };
        }
        foreach (D d in ds) d();
        Console.WriteLine();
    }
}
