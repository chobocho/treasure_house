// 슬라이드 p4-v3-query-trace — 불린 메서드를 찍는 쿼리 형식, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Q<T>
{
    readonly IEnumerable<T> items;
    public Q(IEnumerable<T> xs) { items = xs; }
    static void Log(string m) { Console.Write(m + " "); }

    public Q<T> Where(Func<T, bool> p)
    { Log("Where"); return new Q<T>(items.Where(p)); }

    public Q<U> Select<U>(Func<T, U> f)
    { Log("Select"); return new Q<U>(items.Select(f)); }

    public Q<V> SelectMany<U, V>(Func<T, IEnumerable<U>> f,
                                 Func<T, U, V> r)
    { Log("SelectMany"); return new Q<V>(items.SelectMany(f, r)); }

    public Q<T> OrderBy<K>(Func<T, K> k)
    { Log("OrderBy"); return new Q<T>(items.OrderBy(k)); }

    public Q<T> ThenByDescending<K>(Func<T, K> k)
    {
        Log("ThenByDescending");
        IOrderedEnumerable<T> o = (IOrderedEnumerable<T>)items;
        return new Q<T>(o.ThenByDescending(k));
    }

    public Q<IGrouping<K, T>> GroupBy<K>(Func<T, K> k)
    { Log("GroupBy"); return new Q<IGrouping<K, T>>(items.GroupBy(k)); }

    public Q<IGrouping<K, E>> GroupBy<K, E>(Func<T, K> k, Func<T, E> e)
    {
        Log("GroupBy(k,e)");
        return new Q<IGrouping<K, E>>(items.GroupBy(k, e));
    }

    public IEnumerator<T> GetEnumerator()
    { return items.GetEnumerator(); }
}
