// 슬라이드 p3-v2-fixed-overrun — 범위 검사가 없다, C# 2.0
using System;

unsafe struct Pair
{
    public fixed int A[2];
    public int After;                    // laid out right after A
}

class App
{
    static unsafe void Main()
    {
        Pair p = new Pair();
        p.After = 7;
        p.A[2] = 99;                     // one past the end: no error
        Console.WriteLine("After = " + p.After);

        int[] arr = new int[2];
        try { arr[2] = 99; }
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine("array: " + e.GetType().Name);
        }
    }
}
