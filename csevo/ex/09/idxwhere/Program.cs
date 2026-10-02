// 슬라이드 p9-v8-idx-where — ^ 가 안 되는 곳, C# 8.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        int[,] grid = new int[3, 3];
        int g = grid[^1, 0];               // multi-dimensional

        var d = new Dictionary<int, string> { { 1, "one" } };
        string s = d[^1];                  // this[TKey], not this[int]

        IEnumerable<int> e = new List<int> { 1, 2, 3 };
        int x = e[^1];                     // no indexer, no Count

        var q = new Queue<int>();
        int y = q[^1];                     // Count but no indexer
    }
}
