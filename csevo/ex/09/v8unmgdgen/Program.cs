// 슬라이드 p9-v8-unmanaged-gen — unmanaged 제약과 생성 형식, C# 8.0
using System;
using System.Runtime.CompilerServices;

struct Coords<T>
{
    public T X, Y;
    public Coords(T x, T y) { X = x; Y = y; }
}

class App
{
    // Coords<T> is unmanaged whenever T is
    static unsafe int Size<T>() where T : unmanaged
        => sizeof(Coords<T>);

    static string Refs<T>() =>
        typeof(T).Name.Replace("`1", "") + "<"
        + typeof(T).GetGenericArguments()[0].Name + ">: "
        + RuntimeHelpers.IsReferenceOrContainsReferences<T>();

    static void Main()
    {
        Console.WriteLine(Size<byte>() + " " + Size<double>());
        Console.WriteLine(Refs<Coords<int>>());
        Console.WriteLine(Refs<Coords<string>>());
#if BAD
        Console.WriteLine(Size<Coords<string>>());   // has a reference
#endif
    }
}
