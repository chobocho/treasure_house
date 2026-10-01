// 슬라이드 p4-v3-ext-iface — 인터페이스에 메서드를 더한다, C# 3.0
using System;
using System.Collections.Generic;

static class SeqExt
{
    public static int Total(this IEnumerable<int> source)
    {
        int sum = 0;
        foreach (int x in source) sum += x;
        return sum;
    }
}

class App
{
    static IEnumerable<int> Gen()
    {
        yield return 10;
        yield return 20;
    }

    static void Main()
    {
        int[] array = { 1, 2, 3 };
        List<int> list = new List<int>(array);
        Queue<int> queue = new Queue<int>(array);

        Console.WriteLine(array.Total());       // T[]
        Console.WriteLine(list.Total());        // List<T>
        Console.WriteLine(queue.Total());       // Queue<T>
        Console.WriteLine(Gen().Total());       // an iterator
    }
}
