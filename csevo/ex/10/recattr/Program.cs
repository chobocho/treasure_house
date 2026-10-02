// 슬라이드 p10-v9-rec-attr — 위치 매개변수의 특성 대상, C# 9.0
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.All)]
class TagAttribute : Attribute { }

record R([Tag] int A, [property: Tag] int B, [field: Tag] int C);

class App
{
    static string Has(ICustomAttributeProvider p) =>
        p.IsDefined(typeof(TagAttribute), false) ? "Tag" : "-";

    static void Main()
    {
        const BindingFlags f = BindingFlags.Instance
            | BindingFlags.NonPublic;
        ParameterInfo[] ps = typeof(R).GetConstructor(
            new[] { typeof(int), typeof(int), typeof(int) })
            .GetParameters();
        Console.WriteLine("    param  property  field");
        foreach (ParameterInfo p in ps)
        {
            string n = p.Name;
            Console.WriteLine("{0}   {1,-6} {2,-9} {3}", n, Has(p),
                Has(typeof(R).GetProperty(n)),
                Has(typeof(R).GetField("<" + n + ">k__BackingField",
                    f)));
        }
    }
}
