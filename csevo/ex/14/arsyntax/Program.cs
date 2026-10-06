// 슬라이드 p14-v13-ar-syntax — 반제약을 적는 자리, C# 13.0
using System;

class C<T, S>
    where T : allows ref struct
    where S : T                     // S does not inherit 'allows'
{
    public static string Name => typeof(T).Name + "/" + typeof(S).Name;
}

class App
{
    static int A<T>() where T : struct, allows ref struct
        => 1;
#if LAST
    static int B<T>() where T : allows ref struct, IDisposable => 2;
#elif CLASS
    static int B<T>() where T : class, allows ref struct => 2;
#elif INHERIT
    static string B() => C<Span<int>, Span<int>>.Name;
#endif

    static void Main()
    {
        Console.WriteLine(C<int, int>.Name);
        Console.WriteLine(C<object, string>.Name);
        Console.WriteLine(A<Span<int>>() + A<int>());
    }
}
