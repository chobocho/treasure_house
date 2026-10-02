// 슬라이드 p5-v4-opt-meta — 메타데이터에 남는 것, C# 4.0
using System;
using System.Reflection;

class Program
{
    public static void Greet(string name, int times = 10,
                             string sep = ", ", object tag = null)
    {
    }

    static void Main()
    {
        MethodInfo m = typeof(Program).GetMethod("Greet");
        foreach (ParameterInfo p in m.GetParameters())
        {
            string dv = "-";
            if (p.HasDefaultValue)
            {
                dv = p.DefaultValue == null ? "null"
                   : "\"" + p.DefaultValue + "\"";
            }
            Console.WriteLine("{0,-5} {1,-5} {2,-5} {3}",
                p.Name, p.IsOptional, dv, p.Attributes);
        }
    }
}
