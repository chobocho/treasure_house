// 슬라이드 p13-v12-ce-order — 요소를 계산하는 차례, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static int Log(int x)
    {
        Console.Write("e" + x + " ");
        return x;
    }

    static IEnumerable<int> Gen()
    {
        Console.Write("[gen] ");
        yield return 10;
        Console.Write("[next] ");
        yield return 11;
    }

    static void Main()
    {
        int[] a = [Log(1), .. Gen(), Log(2)];
        Console.WriteLine("| " + string.Join(",", a));
        List<int> l = [Log(1), .. Gen(), Log(2)];
        Console.WriteLine("| " + string.Join(",", l));
        var old = new List<int> { Log(1), Log(2) };
        Console.WriteLine("| " + old.Count);
    }
}
