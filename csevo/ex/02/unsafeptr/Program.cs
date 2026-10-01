// 슬라이드 p2-v1-unsafe — 포인터와 fixed, C# 1.0
using System;

struct Pixel { public byte R, G, B, A; }

class App
{
    static unsafe int Sum(int* p, int n)
    {
        int s = 0;
        for (int* end = p + n; p < end; p++)    // pointer arithmetic
            s += *p;
        return s;
    }

    static unsafe void Main()
    {
        int[] data = { 1, 2, 3, 4, 5 };
        fixed (int* p = data)                   // pin the array
        {
            Console.WriteLine("sum = " + Sum(p, data.Length));
            Console.WriteLine("p[2] = " + p[2] + ", *(p+4) = "
                + *(p + 4));
            long gap = (byte*)(p + 4) - (byte*)p;
            Console.WriteLine("bytes from p to p+4: " + gap);
        }

        Pixel px = new Pixel();
        Pixel* pp = &px;                        // address of a local
        pp->G = 200;
        byte* b = (byte*)pp;
        Console.WriteLine("sizeof(Pixel) = " + sizeof(Pixel)
            + ", byte 1 = " + b[1] + ", px.G = " + px.G);
    }
}
