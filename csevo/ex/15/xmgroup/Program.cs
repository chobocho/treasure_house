// 슬라이드 p15-v14-xm-group — 묶음 형식과 표지 형식의 수, C# 14
using System;
using System.Collections.Generic;
using System.Linq;

static class E
{
    extension(string s) { public int A => 1; }
    extension(string t) { public int B => 2; }    // other name
    extension(string s) { public int C => 3; }    // same as first
    extension<T>(List<T> l) where T : notnull { public int D => 4; }
    extension<U>(List<U> u) { public int F => 5; }
}

class Program
{
    static void Main()
    {
        foreach (Type g in typeof(E).GetNestedTypes()
                     .OrderBy(t => t.GetNestedTypes().Length))
        {
            Console.WriteLine("group <" + string.Join(",",
                g.GetGenericArguments().Select(a => a.Name))
                + "> markers " + g.GetNestedTypes().Length);
            foreach (Type m in g.GetNestedTypes())
            {
                var p = m.GetMethod("<Extension>$").GetParameters()[0];
                Console.WriteLine("  marker <" + string.Join(",",
                    m.GetGenericArguments().Select(a => a.Name))
                    + "> param " + p.Name);
            }
        }
    }
}
