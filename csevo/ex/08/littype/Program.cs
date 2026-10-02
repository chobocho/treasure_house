// 슬라이드 p8-v7-literals-type — 이진 리터럴의 형식, C# 7.0
using System;

class App
{
    static void Show(object o)
    {
        Console.WriteLine("{0,-22} {1}", o, o.GetType().Name);
    }

    static void Main()
    {
        Show(0b0111_1111_1111_1111_1111_1111_1111_1111);  // 31 bits
        Show(0b1000_0000_0000_0000_0000_0000_0000_0000);  // 32 bits
        Show(0x8000_0000);                                // same value
        Show(0b1_0000_0000_0000_0000_0000_0000_0000_0000); // 33 bits
        Show(0b1L);
        Show(0b1u);
        int min =
            unchecked((int)0b1000_0000_0000_0000_0000_0000_0000_0000);
        Show(min);
#if BAD
        int bad = 0b1000_0000_0000_0000_0000_0000_0000_0000;
#endif
    }
}
