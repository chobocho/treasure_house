// 슬라이드 p2-v1-arrays — 직사각 배열과 들쭉날쭉 배열, C# 1.0
using System;

class App
{
    static void Main()
    {
        int[,] grid = new int[2, 3];          // one block, rank 2
        grid[1, 2] = 7;
        Console.WriteLine(grid.GetType().Name + " rank " + grid.Rank
            + " length " + grid.Length + " cols " + grid.GetLength(1));

        int[][] jag = new int[2][];           // array of arrays
        Console.WriteLine("jag[0] null? " + (jag[0] == null));
        jag[0] = new int[] { 1 };
        jag[1] = new int[] { 1, 2, 3 };
        Console.WriteLine(jag.GetType().Name + " rank " + jag.Rank
            + " length " + jag.Length + " row1 " + jag[1].Length);

        int[] init = { 3, 1, 2 };             // initializer only
        Array.Sort(init);
        Console.WriteLine(init[0] + "," + init[1] + "," + init[2]);
        Console.WriteLine(Array.IndexOf(init, 3));

        int[,] small = { { 1, 2 }, { 3, 4 } };
        Console.WriteLine(small[1, 0]);
        Console.WriteLine(jag[0][1]);         // out of range
    }
}
