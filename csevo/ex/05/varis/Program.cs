// 슬라이드 p5-v4-var-is — is 와 as 도 변성을 안다, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static string Pretty(Type t)
    {
        if (!t.IsGenericType) return t.Name;
        int tick = t.Name.IndexOf('`');   // nested types: no tick
        string name = tick < 0 ? t.Name : t.Name.Substring(0, tick);
        Type[] args = t.GetGenericArguments();
        return name + "<" + string.Join(", ",
            Array.ConvertAll(args, delegate(Type a) { return a.Name; }))
            + ">";
    }

    static void Check(object o)
    {
        IEnumerable<object> seq = o as IEnumerable<object>;
        Console.WriteLine("{0,-30} as IEnumerable<object>: {1}",
                          Pretty(o.GetType()), seq != null);
    }

    static void Main()
    {
        Check(new List<string>());
        Check(new List<Uri>());
        Check(new List<int>());
        Check(new string[0]);
        Check(new Dictionary<string, Uri>().Keys);
    }
}
