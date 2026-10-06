// 슬라이드 p13-v12-ia-why — C# 11 까지의 구조체 안 배열, C# 11.0
using System;

unsafe struct Packet
{
    public fixed byte Data[8];     // C# 2: unsafe, primitives only
#if BAD
    public fixed string Names[4];  // managed element type
#endif
}

class App
{
    static unsafe void Main()
    {
        var p = new Packet();
        p.Data[0] = 1;
        p.Data[7] = 8;
        Console.WriteLine(p.Data[0] + " " + p.Data[7]);
        Console.WriteLine(sizeof(Packet));
#if BAD2
        Span<byte> s = p.Data;     // no conversion to a span
#endif
    }
}
