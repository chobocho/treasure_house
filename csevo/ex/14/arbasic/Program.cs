// 슬라이드 p14-v13-allowsref — allows ref struct 반제약, C# 13.0
using System;

// a generic ref struct whose field may itself be a ref struct
ref struct Holder<T> where T : allows ref struct
{
    public T Value;
    public Holder(T v) { Value = v; }
}

class App
{
    // the proposal's example: T may be Span<int>
    static T Identity<T>(T p) where T : allows ref struct => p;

#if BAD
    static T F<T>(T p) => p;        // no anti-constraint
    static int Bad() => F(new Span<int>(new int[3])).Length;
#endif

    static void Main()
    {
        Span<int> local = Identity(new Span<int>(new int[10]));
        Console.WriteLine(local.Length);

        var h = new Holder<Span<int>>(local.Slice(2, 3));
        h.Value[0] = 42;
        Console.WriteLine(local[2]);

        // ordinary types still work
        Console.WriteLine(Identity("text"));
        Console.WriteLine(new Holder<int>(7).Value);
    }
}
