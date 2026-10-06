// 슬라이드 p13-v12-ce-infer — 컬렉션 식과 형식 추론, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static T[] AsArray<T>(T[] arg) => arg;
    static List<T[]> AsListOfArray<T>(List<T[]> arg) => arg;
    static T First<T>(IEnumerable<T> xs)
    {
        foreach (T x in xs) return x;
        return default;
    }

    static void Main()
    {
        var a = AsArray([1, 2, 3]);
        var b = AsListOfArray([[4, 5], []]);
        var c = First([1L, 2]);            // long and int: T = long
        Console.WriteLine(a.GetType().Name + " " + b.GetType().Name
                          + " " + c.GetType().Name);
        long[] ys = [1, 2];
        var d = AsArray([.. ys, 3]);       // spread: lower bound
        Console.WriteLine(d.GetType().Name + " " + d.Length);
#if BAD
        var e = AsArray([]);
#endif
    }
}
