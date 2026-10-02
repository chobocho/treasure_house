// 슬라이드 p8-v7_3-fixbuf — 움직이는 고정 버퍼의 인덱싱, C# 7.3
using System;

unsafe struct Packet
{
    public fixed byte Head[4];          // a fixed-size buffer
}

class Holder
{
    public Packet P;                    // lives in a heap object
}

class App
{
    static unsafe void Main()
    {
        var h = new Holder();
        h.P.Head[2] = 7;                // no 'fixed' needed now
        Console.WriteLine(h.P.Head[2]);
        fixed (byte* q = h.P.Head)      // C# 2 style, still fine
        {
            Console.WriteLine(q[2]);
        }
#if BAD
        byte* p = h.P.Head;             // a raw pointer: pin it
#endif
    }
}
