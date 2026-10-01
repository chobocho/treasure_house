// 슬라이드 p3-v2-iterators-gate — yield return 반복기, C# 2.0
using System;
using System.Collections;

class App
{
    static IEnumerable Range(int start, int count)
    {
        for (int i = 0; i < count; i++)
        {
            yield return start + i;
        }
    }

    static void Main()
    {
        foreach (int x in Range(3, 4))
        {
            Console.Write(x + " ");
        }
        Console.WriteLine();
    }
}
