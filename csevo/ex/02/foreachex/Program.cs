// 슬라이드 p2-v1-foreach — 배열과 IEnumerable 위의 foreach, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        int[,] grid = { { 1, 2, 3 }, { 4, 5, 6 } };
        foreach (int n in grid)              // rightmost index first
            Console.Write(n + " ");
        Console.WriteLine();

        ArrayList list = new ArrayList();
        list.Add("x"); list.Add("y");
        IEnumerator e = list.GetEnumerator();   // what foreach does
        while (e.MoveNext())
            Console.Write((string)e.Current + " ");
        Console.WriteLine();

        try
        {
            foreach (string s in list)
                if (s == "x") list.Add("z");  // change while iterating
        }
        catch (InvalidOperationException ex)
        {
            Console.WriteLine(ex.Message);
        }
    }
}
