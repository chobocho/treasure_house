// 슬라이드 p12-v11-ck-pair — 짝 규칙과 되돌아가기, C# 11.0
using System;

readonly struct U8
{
    public readonly byte V;
    public U8(int v) => V = unchecked((byte)v);
    public override string ToString() => V.ToString();

    public static U8 operator +(U8 a, U8 b) => new U8(a.V + b.V);
    public static U8 operator checked +(U8 a, U8 b) =>
        new U8(checked((byte)(a.V + b.V)));

    // Only a regular -: checked(a - b) uses it too
    public static U8 operator -(U8 a, U8 b) => new U8(a.V - b.V);
#if BAD
    public static U8 operator checked *(U8 a, U8 b) => a; // no *
#endif
}

class App
{
    static void Main()
    {
        U8 x = new U8(10), y = new U8(20);
        Console.WriteLine(checked(x - y));     // 246, no exception
        Console.WriteLine(checked(y + x));
    }
}
