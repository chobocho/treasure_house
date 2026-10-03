// 슬라이드 p12-v11-rf-meta — ref 필드와 scoped 의 메타데이터, C# 11
using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;

ref struct Holder
{
    public ref int A;
    public ref readonly int B;
    public readonly ref int C;

    public void Take(scoped ref int p, ref int q,
        scoped Span<int> s, scoped out int o) { o = 0; }
}

struct S { int _f; [UnscopedRef] public ref int F => ref _f; }

class Program
{
    static string Attrs(object[] a) =>
        string.Join(" ", a.Select(x => "[" + x.GetType().Name + "]"));

    static void Main()
    {
        var flags = BindingFlags.Public | BindingFlags.Instance;
        foreach (FieldInfo f in typeof(Holder).GetFields(flags))
            Console.WriteLine("field {0}: {1} initonly={2} {3}",
                f.Name, f.FieldType, f.IsInitOnly,
                Attrs(f.GetCustomAttributes(false)));
        MethodInfo take = typeof(Holder).GetMethod("Take");
        foreach (ParameterInfo p in take.GetParameters())
            Console.WriteLine("param {0}: {1} {2}", p.Name,
                p.ParameterType, Attrs(p.GetCustomAttributes(false)));
        PropertyInfo prop = typeof(S).GetProperty("F");
        Console.WriteLine("S.F: "
            + Attrs(prop.GetCustomAttributes(false)));
    }
}
