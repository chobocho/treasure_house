// 슬라이드 p10-v9-nl-default — where T : default, C# 9.0
using System;
using System.Diagnostics.CodeAnalysis;

public abstract class A
{
    // C# 8 style: no T?, attributes instead
    [return: MaybeNull] public abstract T F1<T>();
    public abstract void F2<T>([AllowNull] T t);
}

public class B : A
{
    public override T? F1<T>() where T : default => default;
    public override void F2<T>(T? t) where T : default
        => Console.WriteLine(t == null ? "null" : t.ToString());
}

class App
{
    static void Main()
    {
        A a = new B();
        Console.WriteLine(a.F1<string>() ?? "null");
        a.F2<string>(null);
        a.F2(7);
    }
#if BAD
    static T? G<T>() where T : default => default;   // not an override
#endif
}
