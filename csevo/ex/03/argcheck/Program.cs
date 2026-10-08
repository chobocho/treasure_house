// 슬라이드 p3-v2-iterator-args — 인수 검사가 늦게 터진다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Take(int[] src, int n)
    {
        if (src == null) throw new ArgumentNullException("src");
        for (int i = 0; i < n; i++)
        {
            yield return src[i];
        }
    }

    static void Main()
    {
        IEnumerable<int> q = Take(null, 2);   // no exception here
        Console.WriteLine("Take returned");
        try
        {
            foreach (int x in q) Console.WriteLine(x);
        }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("thrown in foreach: " + e.ParamName);
        }
    }
}
