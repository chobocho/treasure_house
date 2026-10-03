// 슬라이드 p12-v11-ck-dyn — dynamic 과 checked 연산자, C# 11.0
using System;

readonly struct U8
{
    public readonly byte V;
    public U8(int v) => V = unchecked((byte)v);
    public static U8 operator +(U8 a, U8 b)
    {
        Console.Write("[+] ");
        return new U8(a.V + b.V);
    }
    public static U8 operator checked +(U8 a, U8 b)
    {
        Console.Write("[checked +] ");
        return new U8(checked((byte)(a.V + b.V)));
    }
}

class App
{
    static void Main()
    {
        U8 x = new U8(200), y = new U8(100);
        dynamic d = x;
        U8 r = checked(d + y);                   // bound at run time
        Console.WriteLine(r.V);
        try { Console.WriteLine(checked(x + y).V); }  // static binding
        catch (OverflowException) { Console.WriteLine("Overflow"); }
        int big = int.MaxValue;
        dynamic di = big;
        try { Console.WriteLine(checked(di + 1)); }    // built-in int +
        catch (OverflowException) { Console.WriteLine("int Overflow"); }
    }
}
