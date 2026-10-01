// 슬라이드 p2-v1-shift — 시프트 횟수는 하위 5·6비트만, C# 1.0
using System;

class App
{
    static void Main()
    {
        int one = 1;
        for (int n = 30; n <= 33; n++)
        {
            Console.WriteLine("1 << " + n + " = " + (one << n));
        }
        Console.WriteLine("1L << 33 = " + (1L << 33));
        Console.WriteLine("-8 >> 1  = " + (-8 >> 1));    // sign kept
        Console.WriteLine("0xF0000000u >> 28 = " + (0xF0000000u >> 28));
        int minus = -16;
        Console.WriteLine("(uint)-16 >> 28 = " + ((uint)minus >> 28));
    }
}
