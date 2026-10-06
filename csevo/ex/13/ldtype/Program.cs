// 슬라이드 p13-v12-ld-type — 기본값을 담은 합성 대리자 형식, C# 12
using System;
using System.Reflection;

class Program
{
    static void Dump(string what, MethodInfo m)
    {
        Console.Write(what + ":");
        foreach (ParameterInfo p in m.GetParameters())
            Console.Write(" " + p.Name + (p.IsOptional
                ? "=" + p.DefaultValue : ""));
        Console.WriteLine();
    }

    static void Main()
    {
        var a = (int i = 13) => 1;
        var b = (int i = 0) => 2;
        var c = (int k = 13) => 3;    // another name, same default
        a = c;                              // same synthesized type
        Console.WriteLine(a.GetType() == c.GetType());
        Console.WriteLine(a.GetType() == b.GetType());
        Dump("Invoke", a.GetType().GetMethod("Invoke"));
        Dump("lambda", a.Method);
#if BAD
        a = b;                              // default 13 vs 0
#endif
    }
}
