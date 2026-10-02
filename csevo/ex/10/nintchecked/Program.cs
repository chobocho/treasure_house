// 슬라이드 p10-v9-nint-checked — nint 의 넘침, C# 9.0
using System;

class App
{
    static void Main()
    {
        nint max = nint.MaxValue;
        Console.WriteLine(unchecked(max + 1) == nint.MinValue);
        try
        {
            nint x = checked(max + 1);
            Console.WriteLine("no exception: " + x);
        }
        catch (OverflowException e)
        {
            Console.WriteLine("nint:   " + e.GetType().Name);
        }
        IntPtr p = IntPtr.MaxValue;
        try
        {
            IntPtr y = checked(p + 1);
            Console.WriteLine("no exception: " + y);
        }
        catch (OverflowException e)
        {
            Console.WriteLine("IntPtr: " + e.GetType().Name);
        }
    }
}
