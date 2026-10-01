// 슬라이드 p3-v2-fixed-buffer — 고정 크기 버퍼, C# 2.0
using System;

unsafe struct Header
{
    public int Length;
    public fixed byte Magic[4];          // 4 bytes inside the struct
}

class App
{
    static unsafe void Main()
    {
        Header h = new Header();
        h.Length = 4;
        h.Magic[0] = (byte)'C';
        h.Magic[1] = (byte)'S';
        h.Magic[2] = (byte)'2';
        h.Magic[3] = (byte)'!';
        for (int i = 0; i < h.Length; i++)
            Console.Write((char)h.Magic[i]);
        Console.WriteLine();
        Console.WriteLine("sizeof(Header) = " + sizeof(Header));
    }
}
