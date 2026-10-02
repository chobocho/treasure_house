// 슬라이드 p8-v7_2-leadingsep — 접두사 뒤의 _, C# 7.2
using System;

class App
{
    static void Main()
    {
        int mask = 0b_1010_0101;       // C# 7.2: '_' right after 0b
        int color = 0x_00_FF_80;       // and right after 0x
        long big = 1_000_000;          // C# 7.0: between digits
        Console.WriteLine(mask + " " + color + " " + big);
        int _123 = 5;                  // not a literal: an identifier
        Console.WriteLine(_123);
#if BAD
        int a = 1_;                    // trailing
        int b = 0x_;                   // no digits
        double c = 1_.5;               // before the point
#endif
    }
}
