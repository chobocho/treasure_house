// 슬라이드 p12-v11-checked-op — checked 사용자 정의 연산자, C# 11.0
using System;

readonly struct U8
{
    public readonly byte V;
    public U8(int v) => V = unchecked((byte)v);

    public static U8 operator +(U8 a, U8 b) =>          // wraps
        new U8(a.V + b.V);
    public static U8 operator checked +(U8 a, U8 b) =>  // throws
        new U8(checked((byte)(a.V + b.V)));
}

class App
{
    static void Main()
    {
        U8 x = new U8(200), y = new U8(100);
        Console.WriteLine("x + y            = " + (x + y).V);
        Console.WriteLine("unchecked(x + y) = " + unchecked(x + y).V);
        try { Console.WriteLine(checked(x + y).V); }
        catch (OverflowException)
        {
            Console.WriteLine("checked(x + y)   -> Overflow");
        }
    }
}
