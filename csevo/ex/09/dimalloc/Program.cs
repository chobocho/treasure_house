// 슬라이드 p9-v8-dim-alloc — 구조체와 기본 구현의 할당, C# 8.0
using System;

interface IArea
{
    int W { get; }
    int Area() => W * W;                 // default implementation
}

struct Sq : IArea { public int W { get; set; } }

struct Own : IArea
{
    public int W { get; set; }
    public int Area() => W * W;          // its own implementation
}

class App
{
    static int Call<T>(T x) where T : IArea => x.Area();

    static long PerCall(Func<int> f)
    {
        f(); f();                                      // warm up
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 1000; i++) f();
        return (GC.GetAllocatedBytesForCurrentThread() - before) / 1000;
    }

    static void Show(string label, Func<int> f) =>
        Console.WriteLine("{0} : {1} B", label, PerCall(f));

    static void Main()
    {
        var sq = new Sq { W = 3 };
        var own = new Own { W = 3 };
        Show("Sq  via IArea", () => ((IArea)sq).Area());
        Show("Sq  generic  ", () => Call(sq));
        Show("Own generic  ", () => Call(own));
        Show("Own direct   ", () => own.Area());
    }
}
