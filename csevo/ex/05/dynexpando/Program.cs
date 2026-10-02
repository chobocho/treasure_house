// 슬라이드 p5-v4-dyn-expando — ExpandoObject, C# 4.0
using System;
using System.Collections.Generic;
using System.Dynamic;
using Microsoft.CSharp.RuntimeBinder;

class Program
{
    static void Main()
    {
        dynamic p = new ExpandoObject();
        p.Name = "Ada";
        p.Year = 1843;
        p.Describe = (Func<string>)(() => p.Name + ", " + p.Year);
        Console.WriteLine(p.Describe());

        IDictionary<string, object> dict = p;
        foreach (KeyValuePair<string, object> kv in dict)
        {
            Console.WriteLine("{0,-9} {1}", kv.Key, kv.Value.GetType());
        }

        dict.Remove("Year");
        try { Console.WriteLine(p.Year); }
        catch (RuntimeBinderException e) {
            Console.WriteLine(e.Message); }
    }
}
