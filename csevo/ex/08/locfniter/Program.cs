// 슬라이드 p8-v7-locfn-iter — 반복기의 인수 검사를 즉시, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Lazy(int[] src)
    {
        if (src == null) throw new ArgumentNullException(nameof(src));
        foreach (int x in src) yield return x * 2;
    }

    static IEnumerable<int> Eager(int[] src)
    {
        if (src == null) throw new ArgumentNullException(nameof(src));
        return Iterator();

        IEnumerable<int> Iterator()
        {
            foreach (int x in src) yield return x * 2;
        }
    }

    static void Try(string name, Func<int[], IEnumerable<int>> f)
    {
        IEnumerable<int> seq = null;
        try { seq = f(null); Console.WriteLine(name + ": call ok"); }
        catch (ArgumentNullException)
        {
            Console.WriteLine(name + ": call threw"); return;
        }
        try { foreach (int x in seq) { } }
        catch (ArgumentNullException)
        {
            Console.WriteLine(name + ": loop threw");
        }
    }

    static void Main()
    {
        Try("Lazy", Lazy);
        Try("Eager", Eager);
    }
}
