// 슬라이드 p9-v8-idx-linq — 라이브러리가 받는 Index·Range, C# 8.0
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    static IEnumerable<int> Squares()
    {
        for (int i = 1; i <= 6; i++)
            yield return i * i;          // no Length, no indexer
    }

    static void Main()
    {
        // .NET 10 overloads: ElementAt(Index), Take(Range)
        Console.WriteLine(Squares().ElementAt(^1));
        Console.WriteLine(string.Join(",", Squares().Take(2..^1)));
        Console.WriteLine(string.Join(",", Squares().Take(^2..)));
    }
}
