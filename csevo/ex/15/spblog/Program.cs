// 슬라이드 p15-v14-sp-blog — 블로그의 Before/After 를 돌려 보면, C# 14
using System;

class Program
{
    static int ProcessKey(ReadOnlySpan<char> key) => key.Length;

    static void Accumulate(Span<int> head)
    {
        for (int i = 0; i < head.Length; i++) head[i] += 1;
    }

    static long Bytes(Action a)
    {
        a();                                     // JIT first
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b0;
    }

    static void Main()
    {
        string line = "ABCDE-12345";
        int[] buffer = new int[16];
        long before = Bytes(() =>
        {
            ProcessKey(line.AsSpan(0, 5));       // Before
            Accumulate(new Span<int>(buffer, 0, 8));
        });
        Console.WriteLine("Before: " + before + " bytes, buffer[0]="
            + buffer[0]);
        long after = Bytes(() =>
        {
            ProcessKey(line[..5]);               // After
            Accumulate(buffer[..8]);
        });
        Console.WriteLine("After:  " + after + " bytes, buffer[0]="
            + buffer[0]);
    }
}
