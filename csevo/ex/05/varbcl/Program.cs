// 슬라이드 p5-v4-var-bcl — .NET 10 의 BCL 이 선언한 변성, C# 4.0
using System;
using System.Collections.Generic;
using System.Reflection;

class Program
{
    static string Mark(Type p)
    {
        GenericParameterAttributes v = p.GenericParameterAttributes
            & GenericParameterAttributes.VarianceMask;
        if (v == GenericParameterAttributes.Covariant)
            return "out " + p.Name;
        if (v == GenericParameterAttributes.Contravariant)
            return "in " + p.Name;
        return p.Name;
    }

    static void Main()
    {
        Type[] types = {
            typeof(IEnumerable<>), typeof(IEnumerator<>),
            typeof(IReadOnlyList<>), typeof(IList<>),
            typeof(IComparer<>), typeof(IEqualityComparer<>),
            typeof(IObservable<>), typeof(IObserver<>),
            typeof(Func<,>), typeof(Action<>), typeof(Predicate<>),
            typeof(Comparison<>), typeof(Converter<,>), typeof(Lazy<>),
        };
        foreach (Type t in types)
        {
            string name = t.Name.Substring(0, t.Name.IndexOf('`'));
            string[] ps = Array.ConvertAll(t.GetGenericArguments(),
                                           Mark);
            string kind = t.IsInterface ? "interface"
                : t.IsSubclassOf(typeof(Delegate)) ? "delegate"
                : "class";
            Console.WriteLine("{0,-10} {1}<{2}>", kind, name,
                              string.Join(", ", ps));
        }
    }
}
