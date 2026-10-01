// 슬라이드 p2-v1-checked — checked 와 unchecked, C# 1.0
using System;

class App
{
    static void Main()
    {
        int max = int.MaxValue;
        int wrapped = max + 1;                // unchecked by default
        Console.WriteLine("max + 1       = " + wrapped);
        int big = 300;
        Console.WriteLine("(byte)300     = " + (byte)big);
        Console.WriteLine("unchecked     = " + unchecked(max * 2));

        try
        {
            int boom = checked(max + 1);
            Console.WriteLine(boom);
        }
        catch (OverflowException e)
        {
            Console.WriteLine("checked(+1)   : " + e.GetType().Name);
        }
        checked
        {
            Console.WriteLine("checked(byte) : " + (byte)big);
        }
    }
}
