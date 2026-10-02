// 슬라이드 p6-v5-fe-for — for 루프는 바뀌지 않았다, C# 5.0
using System;
using System.Collections.Generic;

class App
{
    static void Show(string tag, List<Func<int>> fs)
    {
        Console.Write(tag);
        foreach (Func<int> f in fs) Console.Write(" " + f());
        Console.WriteLine();
    }

    static void Main()
    {
        List<Func<int>> a = new List<Func<int>>();
        for (int i = 0; i < 3; i++)
            a.Add(() => i);
        Show("for, capture i:     ", a);

        List<Func<int>> b = new List<Func<int>>();
        for (int i = 0; i < 3; i++)
        {
            int copy = i;
            b.Add(() => copy);
        }
        Show("for, capture a copy:", b);

        List<Func<int>> c = new List<Func<int>>();
        int n = 0;
        while (n < 3)
        {
            int inner = n * 10;
            c.Add(() => inner + n);
            n++;
        }
        Show("while, inner + n:   ", c);
    }
}
