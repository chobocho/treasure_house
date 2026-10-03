// 슬라이드 p12-v11-ck-body — checked 연산자의 몸체, C# 11.0
using System;

readonly struct I32
{
    public readonly int V;
    public I32(int v) => V = v;

    public static I32 operator +(I32 a, I32 b) => new I32(a.V + b.V);

    // Forgot the inner checked(...): the body is in the default context
    public static I32 operator checked +(I32 a, I32 b)
    {
        Console.Write("[checked +] ");
        return new I32(a.V + b.V);
    }
}

class App
{
    static void Main()
    {
        I32 max = new I32(int.MaxValue), one = new I32(1);
        Console.WriteLine(checked(max + one).V);
    }
}
