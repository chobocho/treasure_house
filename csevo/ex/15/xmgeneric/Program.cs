// 슬라이드 p15-v14-xm-generic — 제네릭 수신자와 제약, C# 14
using System;
using System.Collections.Generic;
using System.Numerics;

static class NumExt
{
    extension<T>(T x) where T : INumber<T>
    {
        public bool IsZero => x == T.Zero;
        public T Clamp(T lo, T hi) => T.Clamp(x, lo, hi);
        public R To<R>() where R : INumber<R> => R.CreateChecked(x);
    }

    extension<K, V>(Dictionary<K, V> d)
    {
        public V Get(K key, V fallback) =>
            d.TryGetValue(key, out V v) ? v : fallback;
    }
#if INFER
    extension<T>(int n) { public static int Zero => 0; }
#endif
}

class Program
{
    static void Main()
    {
        Console.WriteLine(0.0.IsZero + " " + 7.Clamp(1, 5));
        Console.WriteLine(300.To<int, long>());         // T, then R
        Console.WriteLine(NumExt.To<int, byte>(200));
#if ONE
        Console.WriteLine(300.To<long>());              // R alone
#endif
        var d = new Dictionary<string, int> { ["a"] = 1 };
        Console.WriteLine(d.Get("a", -1) + " " + d.Get("b", -1));
#if STR
        Console.WriteLine("text".IsZero);               // constraint
#endif
    }
}
