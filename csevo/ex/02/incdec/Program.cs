// 슬라이드 p2-v1-incdec — i = i++ 는 i 를 바꾸지 않는다, C# 1.0
using System;

class App
{
    static void Main()
    {
        int i = 5;
        i = i++;                              // old value is stored
        Console.WriteLine("i = i++   -> " + i);
        i = 5;
        i = ++i;
        Console.WriteLine("i = ++i   -> " + i);
        int j = 5;
        int k = j++ * 10 + j;                 // 5 * 10 + 6
        Console.WriteLine("j++*10+j  -> " + k);
        byte b = 255;
        b++;                                  // wraps, unchecked
        Console.WriteLine("byte 255++ -> " + b);
    }
}
