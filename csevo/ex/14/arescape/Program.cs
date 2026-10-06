// 슬라이드 p14-v13-ar-escape — T 도 수명 규칙을 따른다, C# 13.0
using System;

class App
{
    // the result may wrap 'span' — the compiler must assume so
    static R Make<R>(Span<int> span) where R : allows ref struct
        => default;

    static T M2<T>(T p) where T : allows ref struct
    {
        Span<int> span = stackalloc int[42];
        T t = Make<T>(span);           // t may point into the stack
#if BAD
        return t;
#else
        return p;
#endif
    }

    // scoped: the callee promises not to let p escape
    static int Peek<T>(scoped T p) where T : allows ref struct => 1;

    static void Main()
    {
        Span<int> s = stackalloc int[3];
        Console.WriteLine(M2(new Span<int>(new int[4])).Length);
        Console.WriteLine(Peek(s));
        Console.WriteLine(M2(9));
    }
}
