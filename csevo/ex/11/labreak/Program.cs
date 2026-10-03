// 슬라이드 p11-v10-la-break — 자연 형식이 바꾼 오버로드 결정, C# 10.0
using System;
using System.Linq.Expressions;

class A
{
    public void M(Func<int> f) => Console.WriteLine("  A.M(Func<int>)");
}

class B : A
{
    public void M(Expression e)
        => Console.WriteLine("  B.M(Expression)");
}

class C
{
    void M(Delegate d) => Console.WriteLine("  C.M(Delegate)");

    static void Main()
    {
        var c = new C();
        c.M(Main);                 // instance method vs extension
        c.M(() => { });
        new B().M(() => 1);        // derived vs base
#if AMBIG
        F(() => () => 1, 2);
#endif
    }

    static void F(Func<Func<object>> f, int i)
        => Console.WriteLine("  F(Func<Func<object>>, int)");
    static void F(Func<Func<int>> f, object o)
        => Console.WriteLine("  F(Func<Func<int>>, object)");
}

static class E
{
    public static void M(this object x, Action y)
        => Console.WriteLine("  E.M(Action)");
}
