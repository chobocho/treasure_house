// 슬라이드 p3-v2-anon-infer — 익명 메서드에서 형식 인수 유추, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static R Call<R>(Converter<int, R> f) { return f(4); }

    static T First<T>(T[] xs, Predicate<T> p)
    {
        foreach (T x in xs) if (p(x)) return x;
        return default(T);
    }

    static string Tag(int x) { return "#" + x; }

    static void Main()
    {
        string[] words = new string[] { "a", "bb", "ccc" };
        Console.WriteLine(First(words,              // T from words
            delegate(string w) { return w.Length > 1; }));
        Console.WriteLine(Call(                     // R from return
            delegate(int n) { return n * 2.5; }));
        Console.WriteLine(Call(Tag));               // R = string
        List<int> xs = new List<int>(new int[] { 1, 2 });
        Console.WriteLine(xs.ConvertAll(Tag)[1]);   // no <string>
    }
}
