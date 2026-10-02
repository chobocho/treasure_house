// 슬라이드 p5-v4-dyn-cache — 호출 지점은 한 번 만들어 다시 쓴다, C# 4.0
using System;
using System.Reflection;

class Program
{
    static int Len(dynamic d)
    {
        return d.Length;
    }

    static object Site()
    {
        BindingFlags all = BindingFlags.NonPublic | BindingFlags.Public
                         | BindingFlags.Static;
        Type holder = typeof(Program).GetNestedTypes(all)[0];
        return holder.GetFields(all)[0].GetValue(null);
    }

    static void Main()
    {
        Console.WriteLine("before: " + (Site() ?? "null"));
        object first = null;
        object[] values = { "abc", new int[5], "xy" };
        foreach (object v in values)
        {
            int n = Len(v);
            object site = Site();
            if (first == null) first = site;
            Console.WriteLine("{0} {1,-12} same site: {2}", n,
                site.GetType().Name, ReferenceEquals(first, site));
        }
    }
}
