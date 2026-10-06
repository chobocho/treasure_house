// 슬라이드 p13-v12-ce-escape — 스팬을 돌려줄 수 있나, C# 12
using System;

class Program
{
    static ReadOnlySpan<int> Consts() => [1, 2, 3];    // data section

    static ReadOnlySpan<T> Three<T>(T x, T y, T z) =>
        (T[])[x, y, z];                                 // heap array
#if BAD
    static ReadOnlySpan<T> Two<T>(T x, T y) => [x, y];  // stack
#endif

    static void Main()
    {
        Console.WriteLine(Consts().Length + " " + Three(1, 2, 3)[2]);
        Span<int> local = [4, 5];
        Console.WriteLine(local[1]);
    }
}
