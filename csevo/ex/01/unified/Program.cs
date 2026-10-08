// 슬라이드 p1-design-box-cs — 모든 것은 객체, C# 1.0
using System;
using System.Collections;

class Program
{
    static void Main()
    {
        Console.WriteLine(42.ToString("X"));   // a literal has methods
        Console.WriteLine(3.CompareTo(4));
        Console.WriteLine(typeof(int) == typeof(Int32));

        object o = 42;                         // boxing
        Console.WriteLine(o.GetType().FullName);

        ArrayList list = new ArrayList();
        list.Add(1);
        list.Add("two");
        list.Add(3.5);
        foreach (object x in list)
            Console.WriteLine(x.GetType().Name + " " + x);

        int back = (int)list[0];               // unboxing
        Console.WriteLine(back + 1);
    }
}
