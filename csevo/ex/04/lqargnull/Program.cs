// 슬라이드 p4-v3-linq-argcheck — 인자 검사는 바로, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<T> MyWhere<T>(IEnumerable<T> src,
                                     Func<T, bool> p)
    {
        if (src == null) throw new ArgumentNullException("src");
        foreach (T x in src)
        {
            if (p(x)) yield return x;
        }
    }

    static void Main()
    {
        string[] none = null;
        try
        {
            IEnumerable<string> a = MyWhere(none, s => true);
            Console.WriteLine("MyWhere: no exception yet");
            IEnumerable<string> b = none.Where(s => true);
            Console.WriteLine("Where: no exception yet");
        }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("Where threw at the call, param '"
                              + e.ParamName + "'");
        }
    }
}
