// 슬라이드 p3-v2-generic-delegates — 제네릭 대리자 형식, C# 2.0
using System;
using System.Collections.Generic;

delegate TOut Map<TIn, TOut>(TIn x);

class App
{
    static string Tag(int x) { return "#" + x; }
    static bool IsEven(int x) { return x % 2 == 0; }

    static void Main()
    {
        Map<int, string> m = new Map<int, string>(Tag);
        Console.WriteLine(m(7));

        List<int> xs = new List<int>(new int[] { 1, 2, 3, 4 });
        List<int> evens = xs.FindAll(new Predicate<int>(IsEven));
        List<string> tags =
            xs.ConvertAll(new Converter<int, string>(Tag));
        Console.WriteLine(evens.Count);
        Console.WriteLine(string.Join(",", tags.ToArray()));
    }
}
