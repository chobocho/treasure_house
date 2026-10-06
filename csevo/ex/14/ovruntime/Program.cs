// 슬라이드 p14-v13-runtime — C# 13 이 기대는 형식, C# 13
using System;
using System.Runtime.CompilerServices;

class Program
{
    static void Show(string name)
    {
        Type t = Type.GetType(name);
        Console.WriteLine(name.Substring(name.LastIndexOf('.') + 1)
            .PadRight(36) + (t == null ? "none"
            : t.Assembly.GetName().Name + (t.IsByRefLike
              ? " (ref struct)" : "")));
    }

    static void Main()
    {
        Show("System.Threading.Lock");                     // 3장
        Show("System.Threading.Lock+Scope");
        Show("System.Runtime.CompilerServices"
             + ".ParamCollectionAttribute");               // 2장
        Show("System.Runtime.CompilerServices"
             + ".OverloadResolutionPriorityAttribute");    // 6장
        Show("System.Diagnostics.CodeAnalysis"
             + ".UnscopedRefAttribute");               // 2장
        Console.WriteLine("RuntimeFeature.ByRefLikeGenerics = "
            + RuntimeFeature.IsSupported(
                RuntimeFeature.ByRefLikeGenerics));        // 4장
        Console.WriteLine(Environment.Version);
    }
}
