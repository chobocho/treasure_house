// 슬라이드 p8-v7-before — 결과 둘을 돌려주는 C# 6 의 네 길, C# 6
using System;
using System.Linq;

class MinMax { public int Min, Max; }       // a type for one method

class App
{
    static void ByOut(int[] xs, out int min, out int max)
    {
        min = xs.Min(); max = xs.Max();
    }
    static Tuple<int, int> ByTuple(int[] xs) =>
        Tuple.Create(xs.Min(), xs.Max());   // a heap object
    static MinMax ByClass(int[] xs) =>
        new MinMax { Min = xs.Min(), Max = xs.Max() };
    static dynamic ByAnon(int[] xs) =>
        new { Min = xs.Min(), Max = xs.Max() };

    static void Main()
    {
        int[] xs = { 3, 9, 4 };
        int min, max;                       // declared before the call
        ByOut(xs, out min, out max);
        Console.WriteLine("out     {0} {1}", min, max);
        var t = ByTuple(xs);
        Console.WriteLine("Tuple   {0} {1}", t.Item1, t.Item2);
        var c = ByClass(xs);
        Console.WriteLine("class   {0} {1}", c.Min, c.Max);
        var d = ByAnon(xs);
        Console.WriteLine("dynamic {0} {1}", d.Min, d.Max);
        try { Console.WriteLine(d.Mn); }    // typo: found at run time
        catch (Exception e) { Console.WriteLine(e.GetType().Name); }
    }
}
