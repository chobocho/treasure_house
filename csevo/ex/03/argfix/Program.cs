// 슬라이드 p3-v2-iterator-args-fix — 검사와 반복기를 나누기, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    public static IEnumerable<int> Take(int[] src, int n)
    {
        if (src == null) throw new ArgumentNullException("src");
        return TakeIterator(src, n);      // a plain method: runs now
    }

    static IEnumerable<int> TakeIterator(int[] src, int n)
    {
        for (int i = 0; i < n; i++)
        {
            yield return src[i];
        }
    }

    static void Main()
    {
        try
        {
            IEnumerable<int> q = Take(null, 2);
            Console.WriteLine("not reached");
        }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("thrown at the call: " + e.ParamName);
        }
    }
}
