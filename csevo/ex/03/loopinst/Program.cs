// 슬라이드 p3-v2-loop-inst — 스코프에 들 때마다 새 변수, C# 2.0
using System;

delegate void D();

class App
{
    static D[] Inside()
    {
        D[] result = new D[3];
        for (int i = 0; i < 3; i++)
        {
            int x = i * 2 + 1;           // a new x every pass
            result[i] = delegate { Console.Write(x + " "); };
        }
        return result;
    }

    static D[] Outside()
    {
        D[] result = new D[3];
        int x;                           // one x for all passes
        for (int i = 0; i < 3; i++)
        {
            x = i * 2 + 1;
            result[i] = delegate { Console.Write(x + " "); };
        }
        return result;
    }

    static void Main()
    {
        foreach (D d in Inside()) d();
        Console.WriteLine();
        foreach (D d in Outside()) d();
        Console.WriteLine();
    }
}
