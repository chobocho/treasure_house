// 슬라이드 p14-v13-pm-override — 재정의와 params 스팬, C# 13
using System;

class Base       // the proposal's shape: returns a span
{
    public virtual Span<int> M(scoped Span<int> a, params Span<int> b)
        => default;
}

class Ok : Base
{
    public override Span<int> M(scoped Span<int> a, params Span<int> b)
        => new[] { a.Length, b.Length };
}

class AlsoOk : Base
{
    public override Span<int> M(scoped Span<int> a, scoped Span<int> b)
        => new[] { b.Length };
}

#if BAD
class Bad : Base
{
    public override Span<int> M(scoped Span<int> a, Span<int> b)
        => default;                    // neither params nor scoped
}
#endif

class Program
{
    static void Main()
    {
        Base x = new Ok(), y = new AlsoOk();
        Console.WriteLine(x.M([1], 2, 3)[1] + " " + y.M([], 4)[0]);
    }
}
