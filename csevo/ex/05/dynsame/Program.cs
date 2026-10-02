// 슬라이드 p5-v4-dyn-object — 실행 중에는 object 와 같다, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        dynamic d = "text";
        object o = d;
        Console.WriteLine(d.GetType());
        Console.WriteLine(o.GetType());
        Console.WriteLine(typeof(List<dynamic>));
        Console.WriteLine(typeof(List<dynamic>)
                          == typeof(List<object>));

        List<object> objs = new List<object>();
        List<dynamic> dyns = objs;         // identity conversion
        dyns.Add(1);
        Console.WriteLine(objs.Count + " "
                          + ReferenceEquals(objs, dyns));
    }
}
