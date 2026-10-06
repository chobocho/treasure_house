// 슬라이드 p13-v12-ce-readonly — 읽기 전용 인터페이스 대상, C# 12
using System;
using System.Collections;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        IReadOnlyList<int> rl = [1, 2, 3];
        var c = (ICollection<int>)rl;    // the mutable view
        var nl = (IList)rl;              // non-generic IList
        Console.WriteLine(c.IsReadOnly + " " + nl.IsReadOnly + " "
                          + nl.IsFixedSize);
        try
        {
            c.Add(4);
        }
        catch (NotSupportedException ex)
        {
            Console.WriteLine(ex.GetType().Name);
        }

        IList<int> ml = [1, 2, 3];       // mutable target
        ml.Add(4);
        Console.WriteLine(ml.Count + " " + (ml is List<int>));
        foreach (Type t in rl.GetType().GetInterfaces())
            Console.WriteLine("  " + t.Name);
    }
}
