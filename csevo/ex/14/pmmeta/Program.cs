// 슬라이드 p14-v13-pm-meta — 메타데이터의 두 특성, C# 13
using System;
using System.Collections.Generic;
using System.Reflection;

class Program
{
    public static void A(params int[] xs) { }
    public static void S(params ReadOnlySpan<int> xs) { }
    public static void L(params List<int> xs) { }
    public static void E(params IEnumerable<int> xs) { }
    public static void N(scoped ReadOnlySpan<int> xs) { }

    static void Main()
    {
        foreach (string name in new[] { "A", "S", "L", "E", "N" })
        {
            ParameterInfo p = typeof(Program).GetMethod(name)
                .GetParameters()[0];
            Console.Write(name + "(" + p.ParameterType.Name + "):");
            foreach (CustomAttributeData a in p.CustomAttributes)
                Console.Write(" " + a.AttributeType.Name);
            Console.WriteLine();
        }
    }
}
