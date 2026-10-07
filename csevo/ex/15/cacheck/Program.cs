// 슬라이드 p15-v14-ca-checked — checked 복합 대입 연산자, C# 14
using System;

class Meter
{
    public byte V;
    public void operator +=(int d) => V = (byte)(V + d);
    public void operator checked +=(int d) =>
        V = checked((byte)(V + d));
#if NOPAIR
    public void operator checked -=(int d) =>
        V = checked((byte)(V - d));
#endif
}

class Program
{
    static void Main()
    {
        var m = new Meter { V = 250 };
        m += 10;                                 // unchecked context
        Console.WriteLine("unchecked: " + m.V);
        m.V = 250;
        try
        {
            checked { m += 10; }
        }
        catch (OverflowException)
        {
            Console.WriteLine("checked: overflow");
        }
    }
}
