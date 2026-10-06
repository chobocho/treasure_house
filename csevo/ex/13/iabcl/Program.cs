// 슬라이드 p13-v12-ia-runtime — .NET 10 안의 인라인 배열, C# 12.0
using System;
using System.Linq;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        var core = typeof(object).Assembly;
        var all = core.GetTypes()
            .Where(t => t.IsDefined(typeof(InlineArrayAttribute),
                                    false))
            .ToList();
        Console.WriteLine(core.GetName().Name + ": " + all.Count);
        var made = all.Where(t => t.Name.StartsWith("<>y__"));
        var pub = all.Where(t => t.IsPublic);
        var rest = all.Except(made).Except(pub);
        Console.WriteLine("compiler-made: " + string.Join(" ",
            made.Select(t => t.Name).OrderBy(s => s,
                                             StringComparer.Ordinal)));
        Console.WriteLine("public: " + pub.Count() + " "
            + pub.Min(L) + ".." + pub.Max(L));
        foreach (var t in rest.Select(t => t.FullName)
                              .OrderBy(s => s, StringComparer.Ordinal))
            Console.WriteLine("  " + t);

        InlineArray4<int> b = default;     // public in .NET 10
        b[3] = 42;
        Console.WriteLine(b.GetType().Namespace + " " + b[3]);
    }

    static int L(Type t) =>
        t.GetCustomAttributes(typeof(InlineArrayAttribute), false)
         .Cast<InlineArrayAttribute>().Single().Length;
}
