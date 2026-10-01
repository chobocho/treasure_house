// 슬라이드 p3-v2-anon-iter — 반복기가 내는 익명 메서드, C# 2.0
using System;
using System.Collections.Generic;

delegate int D();

class App
{
    static IEnumerable<D> Makers()
    {
        for (int i = 0; i < 3; i++)
            yield return delegate { return i; };   // captures i
    }

    static void Main()
    {
        foreach (D d in Makers())        // call each one at once
            Console.Write(d() + " ");
        Console.WriteLine();

        List<D> all = new List<D>(Makers());   // collect first
        foreach (D d in all)
            Console.Write(d() + " ");
        Console.WriteLine();
    }
}
