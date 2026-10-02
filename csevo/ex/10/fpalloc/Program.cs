// 슬라이드 p10-v9-fnptr-alloc — 대리자와 함수 포인터의 할당, C# 9.0
using System;

unsafe class App
{
    static int Inc(int x) => x + 1;

    static long Delegates(int n)
    {
        long before = GC.GetAllocatedBytesForCurrentThread();
        int sum = 0;
        for (int i = 0; i < n; i++)
        {
            Func<int, int> f = Inc;        // method group -> delegate
            sum = f(sum);
        }
        return GC.GetAllocatedBytesForCurrentThread() - before;
    }

    static long Pointers(int n)
    {
        long before = GC.GetAllocatedBytesForCurrentThread();
        int sum = 0;
        for (int i = 0; i < n; i++)
        {
            delegate*<int, int> f = &Inc;
            sum = f(sum);
        }
        return GC.GetAllocatedBytesForCurrentThread() - before;
    }

    static void Main()
    {
        Delegates(10); Pointers(10);           // warm up
        Console.WriteLine($"delegate: {Delegates(1000) / 1000} B/call");
        Console.WriteLine($"pointer : {Pointers(1000) / 1000} B/call");
    }
}
