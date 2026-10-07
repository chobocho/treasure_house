// 슬라이드 p15-v14-ca-alloc — 할당 바이트로 보는 제자리 갱신, C# 14
using System;

class Buf
{
    public readonly int[] Items;
    public Buf(int n) => Items = new int[n];

    public static Buf operator +(Buf a, int d)
    {
        var r = new Buf(a.Items.Length);
        for (int i = 0; i < r.Items.Length; i++)
            r.Items[i] = a.Items[i] + d;
        return r;
    }

    public void operator +=(int d)
    {
        for (int i = 0; i < Items.Length; i++) Items[i] += d;
    }
}

class Program
{
    static long Bytes(Func<Buf, Buf> step, Buf b)
    {
        step(b);                                   // warm up
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 10; i++) b = step(b);
        return GC.GetAllocatedBytesForCurrentThread() - before;
    }

    static void Main()
    {
        var b = new Buf(10_000);
        long plus = Bytes(x => x = x + 1, b);
        long inPlace = Bytes(x => { x += 1; return x; }, b);
        Console.WriteLine("b = b + 1 : " + plus + " B");
        Console.WriteLine("b += 1    : " + inPlace + " B");
        Console.WriteLine("b[0] = " + b.Items[0]);
    }
}
