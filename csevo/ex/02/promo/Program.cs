// 슬라이드 p2-v1-promo — byte + byte 는 int, C# 1.0
using System;

class App
{
    static void Main()
    {
        byte a = 200, b = 100;
        int sum = a + b;                        // promoted to int
        Console.WriteLine("a + b        = " + sum);
        Console.WriteLine("type         = " + (a + b).GetType().Name);
        byte c = (byte)(a + b);                 // explicit narrowing
        Console.WriteLine("(byte)(a+b)  = " + c);
        a += b;                                 // cast inserted
        Console.WriteLine("a += b       = " + a);

        char ch = 'a';
        Console.WriteLine(ch + 1);              // int 98
        Console.WriteLine((char)(ch + 1));      // 'b'
        ch++;                                   // ++ keeps char
        Console.WriteLine(ch);

        short s = 3;
        Console.WriteLine((s * s).GetType().Name);
        uint u = 1;
        Console.WriteLine((u + 1L).GetType().Name + " " + (u - 2));
    }
}
