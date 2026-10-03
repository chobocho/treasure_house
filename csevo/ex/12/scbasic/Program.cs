// 슬라이드 p12-v11-scoped — scoped 매개변수, C# 11
using System;

class Program
{
    // A ref parameter may now be captured by the returned span
    static Span<int> Wrap(ref int p) => new Span<int>(ref p);

    // scoped: p cannot leave, so callers may pass anything
    static Span<int> Bump(scoped ref int p, Span<int> into)
    {
        p++;
#if BAD2
        return new Span<int>(ref p);          // p is scoped
#else
        return into;
#endif
    }

    static Span<int> Use(int[] heap)
    {
        int local = 42;
        Bump(ref local, heap);
        Console.WriteLine("local = " + local);
#if BAD
        return Wrap(ref local);               // would leak local
#else
        return Bump(ref local, heap);
#endif
    }

    static void Main()
    {
        int[] heap = { 1, 2 };
        Console.WriteLine(Use(heap).Length);
        int x = 5;
        Wrap(ref x)[0] = 50;
        Console.WriteLine(x);
    }
}
