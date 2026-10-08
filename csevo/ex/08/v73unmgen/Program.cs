// 슬라이드 p8-v7_3-unmanaged-bad — 제네릭 구조체도 unmanaged, C# 8.0
using System;

struct Pair<T>
{
    public T A, B;
    public Pair(T a, T b) { A = a; B = b; }
}

class App
{
    static unsafe int Size<T>() where T : unmanaged => sizeof(T);

    static void Main()
    {
        Console.WriteLine(Size<Pair<int>>());     // C# 8.0
        Console.WriteLine(Size<Pair<byte>>());
    }
}
