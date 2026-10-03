// 슬라이드 p12-v11-ni-checked — IntPtr 도 checked 에서 넘친다, C# 11.0
using System;

class App
{
    static IntPtr Add(IntPtr x, int y)
    {
        checked
        {
            return x + y;                       // may now throw
        }
    }

    static void Main()
    {
        IntPtr max = IntPtr.MaxValue;
        Console.WriteLine(unchecked(max + 1));
        try { Console.WriteLine(Add(max, 1)); }
        catch (OverflowException) { Console.WriteLine("Overflow 1"); }
        try { Console.WriteLine(checked((int)max)); }
        catch (OverflowException) { Console.WriteLine("Overflow 2"); }
        Console.WriteLine(unchecked((int)max));
    }
}
