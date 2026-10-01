// 슬라이드 p4-v3-query-let — let 이 만든 투명 식별자를 엿보기, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Seq<T>
{
    readonly IEnumerable<T> items;
    public Seq(IEnumerable<T> xs) { items = xs; }

    public Seq<U> Select<U>(Func<T, U> f)
    {
        return new Seq<U>(items.Select(f));
    }

    public Seq<T> Where(Func<T, bool> p)
    {
        return new Seq<T>(items.Where(x =>
        {
            Console.WriteLine("  Where sees " + x);
            return p(x);
        }));
    }

    public IEnumerator<T> GetEnumerator()
    { return items.GetEnumerator(); }
}

class Program
{
    static void Main()
    {
        Seq<string> words = new Seq<string>(new[] { "fig", "melon" });
        Seq<string> q = from w in words
                        let n = w.Length
                        where n > 3
                        select w + "/" + n;
        foreach (string s in q) Console.WriteLine(s);
    }
}
