// 슬라이드 p3-v2-iterator-using — 반복기 안의 using, C# 2.0
using System;
using System.Collections.Generic;

class Resource : IDisposable
{
    public void Dispose() { Console.WriteLine("disposed"); }
}

class App
{
    static IEnumerable<int> Lines()
    {
        using (Resource r = new Resource())
        {
            for (int i = 1; i <= 3; i++)
            {
                yield return i;
            }
        }
    }

    static void Main()
    {
        foreach (int x in Lines())
        {
            Console.WriteLine(x);
            break;                        // Dispose still runs
        }
        Console.WriteLine("after loop");
    }
}
