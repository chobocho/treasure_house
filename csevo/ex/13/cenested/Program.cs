// 슬라이드 p13-v12-ce-nested — 들쭉날쭉 배열과 다차원 배열, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[] row0 = [1, 2, 3];
        int[] row1 = [4, 5];
        int[][] jag = [row0, row1, []];
        List<List<int>> lol = [[1], [2, 3]];
        Console.WriteLine(jag.Length + " " + jag[2].Length + " "
                          + lol[1].Count);
        int[,] grid = { { 1, 2 }, { 3, 4 } };   // still the old form
        Console.WriteLine(grid.Rank + " " + grid[1, 0]);
#if BAD
        int[,] bad = [[1, 2], [3, 4]];
#endif
    }
}
