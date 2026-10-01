// 슬라이드 p4-v3-query-maybe — 시퀀스가 아닌 형식에 쿼리 식, C# 3.0
using System;

class Maybe<T>
{
    public readonly bool Has;
    public readonly T Value;
    public Maybe(T v) { Has = true; Value = v; }
    public Maybe() { }

    public Maybe<V> SelectMany<U, V>(Func<T, Maybe<U>> f,
                                     Func<T, U, V> r)
    {
        if (!Has) return new Maybe<V>();
        Maybe<U> u = f(Value);
        if (!u.Has) return new Maybe<V>();
        return new Maybe<V>(r(Value, u.Value));
    }

    public override string ToString()
    {
        return Has ? "Some(" + Value + ")" : "None";
    }
}

class Program
{
    static Maybe<int> Parse(string s)
    {
        int n;
        return int.TryParse(s, out n) ? new Maybe<int>(n)
                                      : new Maybe<int>();
    }

    static void Main()
    {
        Console.WriteLine(from a in Parse("2") from b in Parse("3")
                          select a * b);
        Console.WriteLine(from a in Parse("2") from b in Parse("x")
                          select a * b);
    }
}
