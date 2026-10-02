// 슬라이드 p5-v4-dyn-attr — 메타데이터의 dynamic 은 특성 하나, C# 4.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;

class Holder
{
    public object Plain = null;
    public dynamic One = null;
    public List<dynamic> Many = null;
    public Dictionary<string, dynamic> Map = null;
}

class Program
{
    static void Main()
    {
        foreach (FieldInfo f in typeof(Holder).GetFields())
        {
            Console.Write("{0,-5} {1,-22}", f.Name, f.FieldType.Name);
            object[] a = f.GetCustomAttributes(typeof(DynamicAttribute),
                                               false);
            if (a.Length == 0)
            {
                Console.WriteLine(" (no attribute)");
                continue;
            }
            Console.Write(" [Dynamic(");
            DynamicAttribute da = (DynamicAttribute)a[0];
            foreach (bool b in da.TransformFlags)
            {
                Console.Write(b ? " T" : " F");
            }
            Console.WriteLine(" )]");
        }
    }
}
