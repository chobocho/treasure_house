// 슬라이드 p4-v3-runtime — list.Average() 와 Enumerable, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    static void Main()
    {
        List<int> list = new List<int>();
        list.Add(3); list.Add(4); list.Add(8);

        double avg = 0;                       // the for-loop way
        for (int i = 0; i < list.Count; i++) avg += list[i];
        avg /= list.Count;
        Console.WriteLine(avg);

        Console.WriteLine(list.Average());    // the C# 3 way
        Console.WriteLine(Enumerable.Average(list));

        Type t = typeof(Enumerable);
        Console.WriteLine(t.FullName + " in "
            + t.Assembly.GetName().Name);
        Console.WriteLine("static class: "
            + (t.IsAbstract && t.IsSealed));
    }
}
