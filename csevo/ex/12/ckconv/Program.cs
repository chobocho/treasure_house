// 슬라이드 p12-v11-ck-conv — checked 명시적 변환, C# 11.0
using System;

readonly struct U8
{
    public readonly byte V;
    public U8(byte v) => V = v;

    public static explicit operator sbyte(U8 u) =>
        unchecked((sbyte)u.V);
    public static explicit operator checked sbyte(U8 u) =>
        checked((sbyte)u.V);
#if BAD
    public static implicit operator checked int(U8 u) => u.V;
#endif
}

class App
{
    static void Main()
    {
        U8 big = new U8(200);
        Console.WriteLine((sbyte)big);
        try { Console.WriteLine(checked((sbyte)big)); }
        catch (OverflowException) { Console.WriteLine("Overflow"); }
        Console.WriteLine(checked((sbyte)new U8(100)));
    }
}
