// 슬라이드 p14-v13-ar-meta — 반제약은 메타데이터의 플래그 하나, C# 13.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class Box<T> where T : allows ref struct { }
class Plain<T> { }

class App
{
    static void Show(Type t)
    {
        var p = t.GetGenericArguments()[0];
        var a = p.GenericParameterAttributes;
        Console.WriteLine($"{t.Name,-8} {a}");
    }

    static void Main()
    {
        Show(typeof(Box<>));
        Show(typeof(Plain<>));
        Show(typeof(Func<>));
        Show(typeof(Span<>));
#if BAD
        Span<Span<int>> rows = default;
        Console.WriteLine(rows.Length);
#endif
        Console.WriteLine(
            (int)GenericParameterAttributes.AllowByRefLike);
        foreach (var a in typeof(Box<>).GetCustomAttributesData())
            Console.WriteLine("attr " + a.AttributeType.Name);
        Console.WriteLine(RuntimeFeature.IsSupported(
            RuntimeFeature.ByRefLikeGenerics));
        Console.WriteLine(typeof(Span<int>).IsByRefLike);
    }
}
