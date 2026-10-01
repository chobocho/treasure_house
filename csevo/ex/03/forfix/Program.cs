// 슬라이드 p3-v2-for-fix — 반복마다 지역 변수에 베끼기, C# 2.0
using System;

delegate void D();

class App
{
    static void Main()
    {
        D[] ds = new D[3];
        for (int i = 0; i < 3; i++)
        {
            int copy = i;                // declared inside the body
            ds[i] = delegate { Console.Write(copy + " "); };
        }
        foreach (D d in ds) d();
        Console.WriteLine();
    }
}
