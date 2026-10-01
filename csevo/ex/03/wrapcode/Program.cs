// 슬라이드 p3-v2-wrap-code — C# 2.0 의 기능을 한 파일에, C# 2.0
using System;
using System.Collections.Generic;

static partial class Report               // static class, partial type
{
    static IEnumerable<T> Where<T>(IEnumerable<T> xs, Predicate<T> p)
    {
        foreach (T x in xs)               // generics + iterator
            if (p(x)) yield return x;
    }

    static int? Max(IEnumerable<int> xs)  // nullable value type
    {
        int? best = null;
        foreach (int x in xs)
            if (best == null || x > best) best = x;
        return best;
    }

    public static void Run(List<int> scores, int limit)
    {
        int? top = Max(Where(scores,      // anonymous method
            delegate(int s) { return s >= limit; }));
        Console.WriteLine(limit + ": " + (top ?? -1));
    }
}

class App
{
    static void Main()
    {
        List<int> scores = new List<int>(new int[] { 70, 85, 92, 60 });
        Report.Run(scores, 80);
        Report.Run(scores, 95);
    }
}
