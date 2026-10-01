// 슬라이드 p4-v3-lambda-infer — 매개변수 형식은 대상에서, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static List<TOut> Map<TIn, TOut>(List<TIn> src, Func<TIn, TOut> f)
    {
        List<TOut> result = new List<TOut>();
        foreach (TIn item in src) result.Add(f(item));
        return result;
    }

    static void Main()
    {
        Func<int, int> f = x => x + x;              // x : int
        Func<string, string> g = x => x + x;        // x : string
        Console.WriteLine(f(21) + " " + g("ab"));

        List<string> words = new List<string>();
        words.Add("one"); words.Add("three");
        // TIn from words, then TOut from the lambda's body
        List<int> lens = Map(words, w => w.Length);
        Console.WriteLine(lens[0] + " " + lens[1]);
        Console.WriteLine(Map(lens, n => n * 0.5)[1]);
    }
}
