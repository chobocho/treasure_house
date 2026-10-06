// 슬라이드 p14-v13-ri-alloc — 제약을 거친 호출은 박싱 없이, C# 13.0
using System;

interface IValue { int Get(); }

struct Num : IValue { public int N; public int Get() => N; }

ref struct Ref : IValue
{
    public Span<int> S;
    public int Get() => S[0];
}

class App
{
    static int ViaInterface(IValue v) => v.Get();          // boxes Num
    static int ViaGeneric<T>(T v) where T : IValue, allows ref struct
        => v.Get();

    static long Measure(Func<int> body)
    {
        body();                                              // warm up
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 1000; i++) body();
        return GC.GetAllocatedBytesForCurrentThread() - before;
    }

    static void Main()
    {
        var n = new Num { N = 1 };
        int[] data = { 2 };
        Console.WriteLine("interface " + Measure(
            () => ViaInterface(n)));
        Console.WriteLine("generic   " + Measure(() => ViaGeneric(n)));
        Console.WriteLine("ref       " + Measure(
            () => ViaGeneric(new Ref { S = data })));
    }
}
