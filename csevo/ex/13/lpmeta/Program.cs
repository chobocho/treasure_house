// 슬라이드 p13-v12-lp-meta — params 는 메타데이터의 특성, C# 12
using System;
using System.Reflection;

class Program
{
    static void Main()
    {
        var b = (params int[] xs) => xs.Length;
        var a = (int[] xs) => xs.Length;
        ParameterInfo p = b.GetType().GetMethod("Invoke")
            .GetParameters()[0];
        Console.WriteLine(p.Name + " "
            + p.IsDefined(typeof(ParamArrayAttribute)));
        Console.WriteLine(b.Method.GetParameters()[0]
            .IsDefined(typeof(ParamArrayAttribute)));
        Console.WriteLine(a.GetType() == b.GetType());
        b = (int[] xs) => xs.Length * 10;   // OK: params-typed target
        Console.WriteLine(b(1, 2));
#if BAD
        a = b;
#endif
    }
}
